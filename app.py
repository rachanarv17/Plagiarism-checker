import os
import uuid
import re
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from plagiarism_checker import process_document
from fpdf import FPDF

app = Flask(__name__)
app.secret_key = 'supersecretkey_change_in_production'

# Use /tmp for Vercel serverless environment (non-persistent)
is_vercel = os.environ.get('VERCEL') == '1'
db_path = '/tmp/users.db' if is_vercel else 'users.db'
upload_path = '/tmp/uploads' if is_vercel else 'uploads'

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = upload_path

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

with app.app_context():
    db.create_all()

# Helper for Hardened PDF text cleaning
def clean_pdf_text(text):
    if not text: return ""
    # Strip non-ASCII characters to prevent FPDFException (horizontal space calculation errors)
    return re.sub(r'[^\x20-\x7E]+', ' ', str(text))

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', username=session.get('username'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('index'))
        else:
            return render_template('auth.html', error='Invalid credentials', is_login=True)
    return render_template('auth.html', is_login=True)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            return render_template('auth.html', error='Username already exists', is_login=False)
            
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        return redirect(url_for('login'))
    return render_template('auth.html', is_login=False)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/api/scan', methods=['POST'])
def scan_document():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    if file:
        filename = str(uuid.uuid4()) + "_" + file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        results = process_document(filepath)
        session['last_results'] = results
        try: os.remove(filepath)
        except: pass
        return jsonify(results)

@app.route('/report', methods=['GET'])
def download_report():
    if 'user_id' not in session or 'last_results' not in session:
        return redirect(url_for('index'))
        
    results = session['last_results']
    
    # PDF HARDENING v3: Fixed widths, standard fonts, ASCII clean
    pdf = FPDF()
    pdf.add_page()
    pdf.set_left_margin(10)
    pdf.set_right_margin(10)
    SAFE_W = 185 # Safe width for A4 with 10mm margins
    
    pdf.set_font("helvetica", "B", size=16)
    pdf.cell(SAFE_W, 10, txt="Plagiarism Scan Report", ln=True, align="C")
    
    pdf.set_font("helvetica", size=12)
    pdf.ln(10)
    pdf.set_x(10)
    pdf.cell(SAFE_W, 10, txt=f"Overall Similarity: {str(results.get('similarity', 0))}%", ln=True)
    
    pdf.ln(5)
    pdf.set_font("helvetica", "B", size=12)
    pdf.set_x(10)
    pdf.cell(SAFE_W, 10, txt="Matched Phrases:", ln=True)
    
    pdf.set_font("helvetica", size=10)
    for match in results.get('matched_phrases', []):
        phrase = clean_pdf_text(match.get('phrase', ''))
        pdf.set_x(15) # Aligned indent
        pdf.multi_cell(SAFE_W - 5, 8, txt=f"- {phrase}")
        pdf.ln(2) # Small breather between phrases
        
    pdf.ln(10)
    pdf.set_font("helvetica", "B", size=12)
    pdf.set_x(10)
    pdf.cell(SAFE_W, 10, txt="Source URLs:", ln=True)
    
    pdf.set_font("helvetica", size=9)
    for url in results.get('source_urls', []):
        clean_url = clean_pdf_text(str(url))
        pdf.set_x(15)
        pdf.cell(SAFE_W - 5, 8, txt=clean_url, ln=True)
        
    report_filename = f"report_{uuid.uuid4().hex[:8]}.pdf"
    report_path = os.path.join(app.config['UPLOAD_FOLDER'], report_filename)
    
    try:
        pdf.output(report_path)
    except Exception as e:
        print(f"PDF Output Crisis: {e}")
        return f"Error generating PDF: {str(e)}", 500
    
    return send_file(report_path, as_attachment=True, download_name="plagiarism_report.pdf")

if __name__ == '__main__':
    app.run(debug=True)
