# 📘 Flask Contact Book

A Flask-based Contact Management Web Application with **User Login**, **MySQL Database**, **CRUD Operations**, **Search Feature**, and **Excel Import/Export**.  
This project is simple, fast, and perfect for beginners learning Flask + MySQL integration.

---

## 🚀 Features

### 🔐 User Authentication
- User Registration  
- Secure Login & Logout  
- Session-based authentication  

### 📖 Contact Management
- Add new contacts  
- Edit existing contacts  
- Delete contacts  
- Prevents duplicate phone numbers  
- User can manage only their own contacts  

### 🔍 Search Functionality
- Real-time searching of contacts by:
  - Name  
  - Phone  
  - Email  

### 📤 Excel Export
- Export all contacts to `.xlsx` file  
- Uses **xlsxwriter**  

### 📥 Excel Import
- Upload `.xlsx` file  
- Auto-inserts contacts into MySQL  

### 📄 Clean UI with Templates
- Bootstrap-based responsive UI  
- Dashboard page  
- Login/Register pages  

---

## 🛠️ Tech Stack

| Component | Technology |
|----------|------------|
| Backend | Flask (Python) |
| Database | MySQL |
| UI | HTML5, CSS3, Bootstrap |
| Excel | xlsxwriter |
| Version Control | Git & GitHub |

---

## 📂 Folder Structure

flask-contact-book/
│
├── app.py
├── contacts.db
├── requirements.txt
│
└── Templates/
├── layout.html
├── dashboard.html
├── add_edit.html
├── import.html
├── report.html
├── login.html
├── register.html
└── Index.html
