from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from io import BytesIO
import pandas as pd

app = Flask(__name__)
app.secret_key = 'swapthika_secret_key'

# ----------------------------------------------------
# ✅ MySQL Database Configuration
# ----------------------------------------------------
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Swapthika%4027@localhost/contactbook'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ----------------------------------------------------
# Database Models
# ----------------------------------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    contacts = db.relationship('Contact', backref='owner', lazy=True)


class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120))
    address = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # ✅ Prevent duplicate phone numbers per user
    __table_args__ = (db.UniqueConstraint('user_id', 'phone', name='unique_user_phone'),)


with app.app_context():
    db.create_all()

# ----------------------------------------------------
# Routes
# ----------------------------------------------------
@app.route('/')
def home():
    # ✅ Redirect to dashboard if already logged in
    if 'user_id' in session:
        return redirect(url_for('index'))
    return render_template('dashboard.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        existing = User.query.filter_by(username=username).first()

        if existing:
            flash('Username already exists!', 'danger')
            return redirect(url_for('register'))

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password!', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'info')
    return redirect(url_for('home'))

# ----------------------------------------------------
# CONTACT MANAGEMENT
# ----------------------------------------------------
@app.route('/index')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    contacts = Contact.query.filter_by(user_id=session['user_id']).all()
    return render_template('index.html', contacts=contacts, username=session['username'])


# 🔍 Search Contacts
@app.route('/search', methods=['GET'])
def search():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    query = request.args.get('query', '').strip()
    if query:
        contacts = Contact.query.filter(
            (Contact.user_id == session['user_id']) &
            (
                (Contact.name.ilike(f"%{query}%")) |
                (Contact.phone.ilike(f"%{query}%")) |
                (Contact.email.ilike(f"%{query}%"))
            )
        ).all()
    else:
        contacts = Contact.query.filter_by(user_id=session['user_id']).all()

    return render_template('index.html', contacts=contacts, username=session['username'], query=query)


# ➕ Add Contact
@app.route('/add', methods=['GET', 'POST'])
def add_contact():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name'].strip()
        phone = request.form['phone'].strip()
        email = request.form['email'].strip()
        address = request.form['address'].strip()

        if not name or not phone:
            flash('Name and Phone are required!', 'danger')
            return redirect(url_for('add_contact'))

        # ✅ Check duplicate number for same user
        existing_contact = Contact.query.filter_by(user_id=session['user_id'], phone=phone).first()
        if existing_contact:
            flash('This phone number already exists in your contacts!', 'danger')
            return redirect(url_for('add_contact'))

        contact = Contact(name=name, phone=phone, email=email, address=address, user_id=session['user_id'])
        db.session.add(contact)
        db.session.commit()
        flash('Contact added successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('add_edit.html', action='Add')


# ✏️ Edit Contact
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_contact(id):
    contact = Contact.query.get_or_404(id)
    if contact.user_id != session['user_id']:
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form['name'].strip()
        phone = request.form['phone'].strip()
        email = request.form['email'].strip()
        address = request.form['address'].strip()

        # ✅ Prevent duplicate numbers during edit
        duplicate = Contact.query.filter_by(user_id=session['user_id'], phone=phone).first()
        if duplicate and duplicate.id != id:
            flash('This phone number already exists in another contact!', 'danger')
            return redirect(url_for('edit_contact', id=id))

        contact.name = name
        contact.phone = phone
        contact.email = email
        contact.address = address
        db.session.commit()
        flash('Contact updated successfully!', 'info')
        return redirect(url_for('index'))
    return render_template('add_edit.html', action='Edit', contact=contact)


# ❌ Delete Contact
@app.route('/delete/<int:id>')
def delete_contact(id):
    contact = Contact.query.get_or_404(id)
    if contact.user_id != session['user_id']:
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('index'))
    db.session.delete(contact)
    db.session.commit()
    flash('Contact deleted!', 'warning')
    return redirect(url_for('index'))

# ----------------------------------------------------
# Excel Import/Export
# ----------------------------------------------------
@app.route('/import', methods=['GET', 'POST'])
def import_contacts():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        file = request.files['file']
        if not file:
            flash('No file uploaded!', 'danger')
            return redirect(url_for('import_contacts'))

        filename = file.filename
        if filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file)
        else:
            flash('Invalid file type!', 'danger')
            return redirect(url_for('import_contacts'))

        added = 0
        for _, row in df.iterrows():
            name = str(row.get('Name')).strip()
            phone = str(row.get('Phone')).strip()
            email = str(row.get('Email', '')).strip()
            address = str(row.get('Address', '')).strip()

            if pd.notna(name) and pd.notna(phone):
                # ✅ Skip duplicates
                existing = Contact.query.filter_by(user_id=session['user_id'], phone=phone).first()
                if not existing:
                    db.session.add(Contact(name=name, phone=phone, email=email, address=address, user_id=session['user_id']))
                    added += 1

        db.session.commit()
        flash(f'Imported {added} new contacts successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('import.html')


@app.route('/export')
def export_contacts():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    contacts = Contact.query.filter_by(user_id=session['user_id']).all()
    data = [{'Name': c.name, 'Phone': c.phone, 'Email': c.email, 'Address': c.address} for c in contacts]
    df = pd.DataFrame(data)
    output = BytesIO()

    try:
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Contacts')
        output.seek(0)
        return send_file(output, download_name="contacts.xlsx", as_attachment=True)
    except ModuleNotFoundError:
        flash("Error: Please install xlsxwriter using 'pip install xlsxwriter'", 'danger')
        return redirect(url_for('index'))

# ----------------------------------------------------
# Run App
# ----------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)

