import os
from flask import Flask, request, render_template, send_file, jsonify, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image
import PyPDF2
import io
import json
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta, UTC
from functools import wraps
import secrets
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-super-secret-key-123')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    reset_token = db.Column(db.String(100), unique=True)
    reset_token_expiry = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    operations = db.relationship('Operation', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.email}>'

class Operation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    operation_type = db.Column(db.String(20), nullable=False)  # convert, merge, reorder
    file_count = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    file_names = db.Column(db.String(500))  # Store file names as comma-separated string

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        try:
            email = request.form.get('email')
            password = request.form.get('password')
            
            if not email or not password:
                flash('Please enter both email and password.', 'error')
                return render_template('login.html')
            
            user = User.query.filter_by(email=email).first()
            
            if user and check_password_hash(user.password, password):
                login_user(user)
                session['user_id'] = user.id
                next_page = request.args.get('next')
                return redirect(next_page or url_for('index'))
            
            flash('Invalid email or password.', 'error')
            return render_template('login.html')
        except Exception as e:
            print(f"Login error: {str(e)}")  # Add this line for debugging
            flash('An error occurred. Please try again.', 'error')
            return render_template('login.html')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        try:
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            
            if not email or not password or not confirm_password:
                flash('Please fill in all fields.', 'error')
                return render_template('register.html')
            
            if password != confirm_password:
                flash('Passwords do not match.', 'error')
                return render_template('register.html')
            
            if User.query.filter_by(email=email).first():
                flash('Email already registered.', 'error')
                return render_template('register.html')
            
            hashed_password = generate_password_hash(password)
            user = User(email=email, password=hashed_password)
            
            db.session.add(user)
            db.session.commit()
            
            login_user(user)
            session['user_id'] = user.id
            flash('Registration successful!', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            print(f"Registration error: {str(e)}")  # Add this line for debugging
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')
            return render_template('register.html')
            
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('login'))

@app.route('/account')
@login_required
def account():
    return render_template('account.html')

@app.route('/history')
@login_required
def history():
    operations = Operation.query.filter_by(user_id=current_user.id).order_by(Operation.timestamp.desc()).all()
    return render_template('history.html', operations=operations)

@app.route('/convert')
@login_required
def convert_page():
    return render_template('convert.html')

@app.route('/merge')
@login_required
def merge_page():
    return render_template('merge.html')

@app.route('/reorder')
@login_required
def reorder_page():
    return render_template('reorder.html')

@app.route('/convert-to-pdf', methods=['POST'])
@login_required
def convert_to_pdf():
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        return jsonify({'error': 'No selected files'}), 400

    # Create a PDF
    pdf = PyPDF2.PdfMerger()
    file_names = []
    
    for file in files:
        if file and allowed_file(file.filename):
            file_names.append(file.filename)
            # Convert image to PDF
            image = Image.open(file)
            if image.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1])
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Save image to temporary PDF
            temp_pdf = io.BytesIO()
            image.save(temp_pdf, format='PDF', resolution=100.0)
            temp_pdf.seek(0)
            
            # Merge with main PDF
            pdf.append(temp_pdf)

    # Save the final PDF
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'output.pdf')
    pdf.write(output_path)
    pdf.close()

    # Track operation
    operation = Operation(
        user_id=current_user.id,
        operation_type='convert',
        file_count=len(files),
        file_names=','.join(file_names)
    )
    db.session.add(operation)
    db.session.commit()

    return send_file(output_path, as_attachment=True)

@app.route('/merge-pdfs', methods=['POST'])
@login_required
def merge_pdfs():
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        return jsonify({'error': 'No selected files'}), 400

    pdf = PyPDF2.PdfMerger()
    file_names = []
    
    for file in files:
        if file and allowed_file(file.filename):
            file_names.append(file.filename)
            pdf.append(file)

    output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'merged.pdf')
    pdf.write(output_path)
    pdf.close()

    # Track operation
    operation = Operation(
        user_id=current_user.id,
        operation_type='merge',
        file_count=len(files),
        file_names=','.join(file_names)
    )
    db.session.add(operation)
    db.session.commit()

    return send_file(output_path, as_attachment=True)

@app.route('/reorder-pdf', methods=['POST'])
@login_required
def reorder_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    
    try:
        # Read the order from the request
        order = json.loads(request.form.get('order', '[]'))
        if not order:
            return jsonify({'error': 'No order specified'}), 400
        
        # Read the PDF file
        pdf_reader = PyPDF2.PdfReader(file)
        
        # Create a new PDF writer
        pdf_writer = PyPDF2.PdfWriter()
        
        # Add pages in the specified order
        for page_num in order:
            if 0 <= page_num - 1 < len(pdf_reader.pages):
                pdf_writer.add_page(pdf_reader.pages[page_num - 1])
        
        # Save the reordered PDF
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'reordered.pdf')
        with open(output_path, 'wb') as output_file:
            pdf_writer.write(output_file)

        # Track operation
        operation = Operation(
            user_id=current_user.id,
            operation_type='reorder',
            file_count=1,
            file_names=file.filename
        )
        db.session.add(operation)
        db.session.commit()
        
        return send_file(
            output_path,
            as_attachment=True,
            download_name='reordered.pdf',
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate reset token
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.reset_token_expiry = datetime.now(UTC) + timedelta(hours=1)
            db.session.commit()
            
            # For demo purposes, just show the token
            flash(f'Your reset token is: {token}. Please use this to reset your password.', 'info')
            return redirect(url_for('reset_password', token=token))
        
        flash('Email not found.', 'error')
        return render_template('forgot_password.html')
        
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    user = User.query.filter_by(reset_token=token).first()
    if not user or not user.reset_token_expiry or user.reset_token_expiry < datetime.now(UTC):
        flash('Invalid or expired reset token.', 'error')
        return redirect(url_for('forgot_password'))
        
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not password or not confirm_password:
            flash('Please fill in all fields.', 'error')
            return render_template('reset_password.html')
            
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('reset_password.html')
        
        user.password = generate_password_hash(password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()
        
        flash('Your password has been reset successfully.', 'success')
        return redirect(url_for('login'))
        
    return render_template('reset_password.html')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf', 'png', 'jpg', 'jpeg'}

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 