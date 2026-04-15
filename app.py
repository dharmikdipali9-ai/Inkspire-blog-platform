from flask import Flask, render_template, request, redirect, session, flash,jsonify,url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
from functools import wraps
from flask import abort
from sqlalchemy import func



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SECRET_KEY'] = "dipali_blog"
app.config['UPLOAD_FOLDER'] = 'static/uploads'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(255), unique = True, nullable = False)
    password = db.Column(db.String(255), nullable = False)
    profile_pic = db.Column(db.String(255), default='default.jpg')   # ✅ NEW
    bio = db.Column(db.Text)                  # ✅ NEW
    role = db.Column(db.String(10), default="user")  # user / admin
    is_banned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Blog(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(100), nullable=False)
        description = db.Column(db.Text, nullable=False)
        image = db.Column(db.String(255))   # ✅ NEW
        category = db.Column(db.String(50))       # ✅ NEW
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        author = db.Column(db.String(255), nullable=False)

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'))

    __table_args__ = (db.UniqueConstraint('user_id', 'blog_id', name='unique_like'),)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'))
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_approved = db.Column(db.Boolean, default=True)

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reason = db.Column(db.String(255))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_resolved = db.Column(db.Boolean, default=False)  # ✅ NEW

class UnblockRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    message = db.Column(db.Text)
    status = db.Column(db.String(20), default="pending")
    user = db.relationship('User', backref='requests')

with app.app_context():
    db.create_all()
    
@app.route('/')
def home():
    query = request.args.get('q')
    category = request.args.get('category')
    page = request.args.get('page', 1, type=int)

    blogs_query = Blog.query

    if query:
        blogs_query = blogs_query.filter(
            Blog.title.ilike(f"%{query}%") |
            Blog.description.ilike(f"%{query}%")
        )

    if category and category != "All":
        blogs_query = blogs_query.filter_by(category=category)

    # ✅ PAGINATION ADDED
    pagination = blogs_query.order_by(Blog.created_at.desc()).paginate(
        page=page,
        per_page=6
    )

    all_blogs = pagination.items

    blog_data = []
    for blog in all_blogs:
        likes_count = Like.query.filter_by(blog_id=blog.id).count()

        liked = False
        if 'user_id' in session:
            liked = Like.query.filter_by(
                blog_id=blog.id,
                user_id=session['user_id']
            ).first() is not None

        blog_data.append({
            "blog": blog,
            "likes": likes_count,
            "liked": liked
        })

    categories = db.session.query(Blog.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]

    return render_template(
        'index.html',
        blog_data=blog_data,
        categories=categories,
        selected_category=category,
        pagination=pagination   # ✅ IMPORTANT
    )


@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')

    new_password = generate_password_hash(password)

    user = User.query.filter_by(username=username).first()

    # 🧠 USER ALREADY EXISTS
    if user:
        flash("You already have an account, please login.", "login_success")
        return redirect(url_for('home'))

    # ✅ NEW USER
    new_user = User(username=username, password=new_password)
    db.session.add(new_user)
    db.session.commit()

    flash("Registration successful! Please login.", "login_success")
    return redirect(url_for('home'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password, password):

        if user.is_banned:
            return jsonify({"status": "banned", "user_id": user.id})

        session.clear()   # ✅ ADD THIS (VERY IMPORTANT)
        session['user_id'] = user.id
        session['user'] = user.username
        session['profile_pic'] = user.profile_pic
        return {"status": "success"}

    return {"status": "error", "message": "Invalid username or password"}

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user', None)
    flash('Logout Successful!', 'info')
    return redirect('/')

@app.route('/create-blog', methods=['POST', 'GET'])
def create_blog():
    if 'user_id' not in session:
        flash("Please login first!", "warning")
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')

        file = request.files.get('image')
        filename = None

        if file and file.filename != "":
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        new_blog = Blog(
            title=title,
            description=description,
            category=category,
            image=filename,   # ✅ save filename
            author=session['user']
        )

        db.session.add(new_blog)
        db.session.commit()

        flash('Post created successfully!', 'success')
        return redirect('/')

    return render_template('create-blog.html')

@app.route("/blog/<int:id>")
def blog_detail(id):
    blog = Blog.query.get(id)

    comments = Comment.query.filter_by(blog_id=id).order_by(Comment.created_at.desc()).all()
    comments_count = len(comments)
    recent_blogs = Blog.query.order_by(Blog.created_at.desc()).limit(5).all()
    categories = db.session.query(Blog.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]

    comment_data = []

    for c in comments:
        user = User.query.get(c.user_id)
        comment_data.append({
            "comment": c,
            "username": user.username if user else "Unknown",
            "profile_pic": user.profile_pic if user else "default.png"  # ✅ FIXED
        })

    return render_template(
        "blog.html",
        blog=blog,
        comments=comments,
        comment_data=comment_data,
        comments_count = len(comments),
        recent_blogs=recent_blogs
    )
@app.route('/delete/<int:id>')
def blog_delete(id):
    blog = Blog.query.filter_by(id=id).first()
    if not 'user' in session:
        return redirect('/login')
    if not blog.author == session['user']:
        return redirect('/')
    db.session.delete(blog)
    db.session.commit()
    return redirect('/')

@app.route('/update/<int:id>', methods=['POST', 'GET'])
def update_blog(id):
    blog = Blog.query.get_or_404(id)

    if 'user' not in session:
        return redirect('/login')

    if blog.author != session['user']:
        return redirect('/')

    if request.method == "POST":
        title = request.form.get('title')
        category = request.form.get('category')
        description = request.form.get('description')
        file = request.files.get('image')

        blog.title = title
        blog.category=category
        blog.description = description

        # ✅ HANDLE IMAGE UPDATE
        if file and file.filename != "":
            filename = secure_filename(file.filename)
            file.save(os.path.join('static/uploads', filename))

            blog.image = filename   # ✅ update image

        db.session.commit()

        return redirect(f'/blog/{blog.id}')

    return render_template('update-blog.html', blog=blog)

@app.route('/like/<int:blog_id>', methods=['POST'])
def like_blog(blog_id):
    if 'user' not in session:
        return jsonify({"error": "login required"}), 401

    user_id = session['user']

    like = Like.query.filter_by(user_id=user_id, blog_id=blog_id).first()

    if like:
        db.session.delete(like)
        liked = False
    else:
        new_like = Like(user_id=user_id, blog_id=blog_id)
        db.session.add(new_like)
        liked = True

    db.session.commit()

    likes_count = Like.query.filter_by(blog_id=blog_id).count()

    return jsonify({
        "liked": liked,
        "count": likes_count
    })


@app.route('/create-admin')
def create_admin():
    existing = User.query.filter_by(username="admin").first()

    if existing:
        return "Admin already exists"

    admin = User(
        username="admin",
        password=generate_password_hash("admin123"),
        role="admin"
    )

    db.session.add(admin)
    db.session.commit()

    return "Admin created!"


@app.route('/profile/<username>')
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()

    # All blogs by user
    blogs = Blog.query.filter_by(author=username).order_by(Blog.created_at.desc()).all()

    # Total blogs
    total_blogs = len(blogs)

    # Total likes received on all blogs
    total_likes = 0
    for blog in blogs:
        total_likes += Like.query.filter_by(blog_id=blog.id).count()

    return render_template(
        'profile.html',
        user=user,
        blogs=blogs,
        total_blogs=total_blogs,
        total_likes=total_likes
    )

@app.route('/edit-profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user' not in session:
        return redirect('/login')

    user = User.query.filter_by(username=session['user']).first()

    if request.method == 'POST':
        bio = request.form.get('bio')
        file = request.files.get('profile_pic')

        user.bio = bio

        if file and file.filename != "":
            filename = secure_filename(file.filename)
            file.save(os.path.join('static/uploads', filename))

            user.profile_pic = filename
            session['profile_pic'] = filename 
        db.session.commit()

        return redirect(f"/profile/{user.username}")

    return render_template('edit-profile.html', user=user)

@app.route('/comment/<int:blog_id>', methods=['POST'])
def add_comment(blog_id):

    if 'user' not in session:
        return redirect('/login')

    text = request.form.get('text')

    if text:
        new_comment = Comment(
            user_id=session['user_id'],   # ✅ logged-in user
            blog_id=blog_id,
            text=text
        )

        db.session.add(new_comment)
        db.session.commit()

    return redirect(f'/blog/{blog_id}')

@app.route('/delete-comment/<int:id>')
def delete_comment(id):

    comment = Comment.query.get(id)

    if 'user' not in session:
        return redirect('/login')

    blog = Blog.query.get(comment.blog_id)

    # ✅ Only comment owner OR blog owner can delete
    if session['user_id'] == comment.user_id or session['user'] == blog.author:
        db.session.delete(comment)
        db.session.commit()
    return redirect(f'/blog/{blog.id}')

@app.route('/category/<name>')
def category(name):
    blogs = Blog.query.filter_by(category=name).order_by(Blog.created_at.desc()).all()
    page = request.args.get('page', 1, type=int)

    pagination = Blog.query.filter_by(category=name)\
        .order_by(Blog.created_at.desc())\
        .paginate(page=page, per_page=6)

    blogs = pagination.items
    return render_template("index.html", blogs=blogs, selected_category=name, pagination=pagination)


@app.context_processor
def inject_user():
    if 'user' in session:
        user = User.query.filter_by(username=session['user']).first()
        return dict(user=user)
    return dict(user=None)

@app.context_processor
def inject_admin_data():
    report_count = Report.query.count()
    request_count = UnblockRequest.query.filter_by(status="pending").count()

    return dict(
        report_count=report_count,
        request_count=request_count   # ✅ global access
    )

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect('/admin-login')
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        admin = User.query.filter_by(username=username).first()

        if admin and check_password_hash(admin.password, password):
            if admin.role != "admin":
                flash("Not authorized!", "danger")
                return redirect('/admin-login')

            # ✅ store session
            session['admin_id'] = admin.id
            session['admin_user'] = admin.username
            session.permanent = True   # ✅ IMPORTANT

            return redirect('/admin')

        flash("Invalid credentials!", "danger")

    return render_template('admin/admin-login.html')

@app.route('/admin-logout')
def admin_logout():
    session.pop('admin_id', None)
    session.pop('admin_user', None)
    flash("Admin logged out!", "info")
    return redirect('/')

from sqlalchemy import func
from datetime import datetime, timedelta

@app.route('/admin')
@admin_required
def admin_dashboard():
    request_count = UnblockRequest.query.filter_by(status="pending").count()

    # 📊 Basic Stats
    total_users = User.query.count()
    total_posts = Blog.query.count()
    total_comments = Comment.query.count()
    report_count = Report.query.count()

    # 🔥 Most Active Users
    most_active_users = db.session.query(
        Blog.author,
        func.count(Blog.id).label('count')
    ).group_by(Blog.author)\
     .order_by(func.count(Blog.id).desc())\
     .limit(5).all()

    # 📈 Posts in Last 7 Days (Line Chart)
    last_7_days = datetime.utcnow() - timedelta(days=7)

    posts_by_day = db.session.query(
        func.date(Blog.created_at),
        func.count(Blog.id)
    ).filter(Blog.created_at >= last_7_days)\
     .group_by(func.date(Blog.created_at))\
     .all()

    dates = [str(i[0]) for i in posts_by_day]
    counts = [i[1] for i in posts_by_day]

    # 📊 Comments per Post (Bar Chart)
    comments_per_post = db.session.query(
        Blog.title,
        func.count(Comment.id)
    ).join(Comment, Comment.blog_id == Blog.id)\
     .group_by(Blog.title)\
     .limit(5).all()

    post_titles = [i[0] for i in comments_per_post]
    comment_counts = [i[1] for i in comments_per_post]

    # 👥 Users Per Month (NEW Bar Chart)
    users_per_month = db.session.query(
        func.strftime('%Y-%m', User.created_at),  # SQLite
        func.count(User.id)
    ).group_by(func.strftime('%Y-%m', User.created_at)).all()

    user_months = [i[0] for i in users_per_month]
    user_counts = [i[1] for i in users_per_month]

    # 🥧 Categories Distribution (NEW Pie Chart)
    category_data = db.session.query(
        Blog.category,
        func.count(Blog.id)
    ).group_by(Blog.category).all()

    categories = [i[0] for i in category_data]
    category_counts = [i[1] for i in category_data]

    return render_template(
        'admin/dashboard.html',

        # Basic
        request_count=request_count,
        total_users=total_users,
        total_posts=total_posts,
        total_comments=total_comments,
        report_count=report_count,
        most_active_users=most_active_users,

        # Existing charts
        dates=dates,
        counts=counts,
        post_titles=post_titles,
        comment_counts=comment_counts,

        # NEW charts
        user_months=user_months,
        user_counts=user_counts,
        categories=categories,
        category_counts=category_counts
    )

@app.route('/admin/users')
@admin_required
def admin_users():
    users = User.query.all()
    request_count = UnblockRequest.query.filter_by(status="pending").count()
    return render_template('admin/users.html', users=users, request_count=request_count)


@app.route('/admin/toggle-ban/<int:user_id>')
@admin_required
def toggle_ban(user_id):
    user = User.query.get_or_404(user_id)
    user.is_banned = not user.is_banned
    db.session.commit()
    return redirect('/admin/users')

@app.route('/admin/delete-user/<int:user_id>')
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return redirect('/admin/users')

@app.route('/admin/blogs')
@admin_required
def admin_blogs():
    blogs = Blog.query.order_by(Blog.created_at.desc()).all()
    request_count = UnblockRequest.query.filter_by(status="pending").count()
    return render_template('admin/blogs.html', blogs=blogs, request_count=request_count)

@app.route('/admin/delete-blog/<int:id>')
@admin_required
def admin_delete_blog(id):
    blog = Blog.query.get_or_404(id)
    db.session.delete(blog)
    db.session.commit()
    return redirect('/admin/blogs')

@app.route('/admin/comments')
@admin_required
def admin_comments():
    comments = Comment.query.order_by(Comment.created_at.desc()).all()
    return render_template('admin/comments.html', comments=comments)

@app.route('/admin/delete-comment/<int:id>')
@admin_required
def admin_delete_comment(id):
    comment = Comment.query.get_or_404(id)
    db.session.delete(comment)
    db.session.commit()
    return redirect('/admin/comments')

@app.route('/admin/approve-comment/<int:id>')
@admin_required
def approve_comment(id):
    comment = Comment.query.get_or_404(id)
    comment.is_approved = True
    db.session.commit()
    return redirect('/admin/comments')

@app.route('/report/<int:blog_id>', methods=['POST'])
def report_blog(blog_id):
    if 'user_id' not in session:
        return redirect('/login')

    request_count = UnblockRequest.query.filter_by(status="pending").count()
    reason = request.form.get('reason')

    report = Report(
        reason=reason,
        user_id=session['user_id'],
        blog_id=blog_id,
    )

    db.session.add(report)
    db.session.commit()

    flash("Reported successfully!", "success")
    return redirect(request.referrer)

@app.route('/admin/reports')
@admin_required
def admin_reports():
    reports = db.session.query(Report, User, Blog)\
    .join(User, Report.user_id == User.id)\
    .join(Blog, Report.blog_id == Blog.id)\
    .order_by(Report.created_at.desc())\
    .all()
        
        
    
    return render_template('admin/reports.html', reports=reports)

@app.route('/admin/delete-reported-blog/<int:blog_id>')
@admin_required
def delete_reported_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)

    # delete blog
    db.session.delete(blog)

    # also delete related reports
    Report.query.filter_by(blog_id=blog_id).delete()

    db.session.commit()

    flash("Blog deleted successfully!", "success")
    return redirect('/admin/reports')

@app.route('/admin/resolve-report/<int:report_id>')
@admin_required
def resolve_report(report_id):
    report = Report.query.get_or_404(report_id)
    report.is_resolved = True
    db.session.commit()

    flash("Report marked as resolved!", "success")
    return redirect('/admin/reports')

@app.route('/admin/update-username', methods=['POST'])
@admin_required
def update_username():
    user = User.query.get(session['user_id'])
    new_username = request.form['username'].strip()

    if not new_username:
        flash("Username cannot be empty!", "danger")
        return redirect('/admin')

    user.name = new_username
    db.session.commit()
    session['user'] = new_username  # update session
    flash("Username updated successfully!", "success")
    return redirect('/admin')

@app.route('/admin/requests')
def admin_requests():
    requests = UnblockRequest.query.all()
    return render_template('admin/admin_requests.html', requests=requests)

@app.route('/submit-request', methods=['POST'])
def submit_request():
    data = request.get_json()

    existing = UnblockRequest.query.filter_by(
        user_id=data['user_id'],
        status="pending"
    ).first()

    if existing:
        return {
            "status": "exists",
            "message": "You already have a pending request!"
        }

    new_request = UnblockRequest(
        user_id=data['user_id'],
        message=data['message']
    )

    db.session.add(new_request)
    db.session.commit()

    return {
        "status": "success",
        "message": "Request sent successfully!"
    }
    
    
@app.route('/admin/approve-request/<int:id>')
@admin_required
def approve_request(id):
    req = UnblockRequest.query.get_or_404(id)

    user = User.query.get(req.user_id)
    user.is_banned = False

    req.status = "approved"

    db.session.commit()

    flash("User unblocked successfully!", "success")
    return redirect('/admin/requests')

@app.route('/admin/reject-request/<int:id>')
@admin_required
def reject_request(id):
    req = UnblockRequest.query.get_or_404(id)

    req.status = "rejected"
    db.session.commit()

    flash("Request rejected!", "danger")
    return redirect('/admin/requests')

@app.route('/admin/delete-request/<int:id>')
@admin_required
def delete_request(id):
    req = UnblockRequest.query.get_or_404(id)
    db.session.delete(req)
    db.session.commit()
    flash("Request record deleted.", "info")
    return redirect('/admin/requests')

@app.route('/admin/delete-multiple-requests', methods=['POST'])
@admin_required 
def delete_multiple_requests():
    data = request.get_json()
    ids = data.get('ids', [])

    for req_id in ids:
        req = UnblockRequest.query.get(req_id)
        if req:
            db.session.delete(req)

    db.session.commit()

    return jsonify({"success": True})

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template("404.html"), 500

if __name__ == "__main__":
    app.run(debug=True)