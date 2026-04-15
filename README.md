# 🪶 Inkspire – Blogging Platform

Inkspire is a modern full-stack blogging platform built using Flask, designed to provide a seamless experience for creating, managing, and interacting with blog content. It features user authentication, admin controls, and a clean, responsive UI.

---

## 🚀 Features

### 👤 User Features
- User Registration & Login (with password hashing)
- Create, Edit, and Delete Blogs
- Upload Blog Images
- Like & Unlike Posts
- Comment on Blogs
- User Profile with Bio & Profile Picture
- Search & Category Filter

### 🛡️ Admin Features
- Admin Dashboard with Analytics
- Manage Users (Ban / Unban / Delete)
- Manage Blogs & Comments
- Handle Reports (Resolve/Delete)
- Unblock Request System
- Bulk Actions (Delete Multiple Requests)

### ⚙️ Additional Features
- Responsive UI (Mobile + Desktop)
- Dark / Light Mode Toggle 🌙
- Custom 404 Error Page
- Modal-based Authentication (No page reload)
- Flash Messages & Alerts

...

## 🚀 Live Demo

👉 Live Website: https://inkspire-blog-platform-2-sfh3.onrender.com/

...


## 📸 Screenshots   👈 ADD HERE

### 🏠 Home Page
<img width="1365" height="680" alt="home" src="https://github.com/user-attachments/assets/cb6a55d9-82d5-4fb6-80db-827b0104c0b5" />


### ✍️ Create Blog
<img width="1364" height="682" alt="create-blog" src="https://github.com/user-attachments/assets/2ff0eb43-6dd6-4a0a-8cd6-37be8e247591" />


### 👤 Profile Page
<img width="1355" height="680" alt="profile" src="https://github.com/user-attachments/assets/65b89d9d-3e27-4462-9e69-90307c24d9f4" />


### 🛡️ Admin Dashboard
<img width="1365" height="680" alt="admin-dashboard" src="https://github.com/user-attachments/assets/df561679-ea8e-44cb-a355-13df3979541a" />


### 🚨 Requests Page
<img width="1360" height="676" alt="request" src="https://github.com/user-attachments/assets/b6e2e513-fe6c-4587-852c-540ca93775d5" />


---

## 🛠️ Tech Stack

**Frontend:**
- HTML5, CSS3, Bootstrap 5
- JavaScript (ES6)
- Font Awesome & Bootstrap Icons

**Backend:**
- Python (Flask)

**Database:**
- SQLite (SQLAlchemy ORM)

---

## 📁 Project Structure

    Inkspire/
    │
    ├── static/             # CSS, JS, Images
    ├── templates/          # HTML Templates
    │   └── admin/          # Admin Pages
    ├── app.py              # Main Flask App
    ├── blog.db             # Database (ignored in production)
    ├── .gitignore
    └── README.md

---

## ⚡ Installation & Setup

### 1️⃣ Clone the repository
git clone https://github.com/your-username/Inkspire-blog-platform.git  
cd Inkspire-blog-platform  

### 2️⃣ Create virtual environment
python -m venv env  
env\Scripts\activate   (Windows)

### 3️⃣ Install dependencies
pip install flask flask_sqlalchemy werkzeug  

### 4️⃣ Run the app
python app.py  

👉 Open in browser:  
http://127.0.0.1:5000

---

## 🔐 Admin Access

An admin account can be created using the `/create-admin` route.

For security reasons, default credentials are not shared. 

---

## 📌 Notes

- Database (.db) is not included in repository (auto-created on run)
- Designed for learning and portfolio purposes

---

## 🌟 Future Enhancements

- REST API integration  
- JWT Authentication  
- Real-time notifications  
- Blog bookmarking  

---

## 📧 Contact

Dipali Dharmik  
Aspiring Software Developer  

---

## ⭐ Show your support

If you like this project, give it a ⭐ on GitHub!
