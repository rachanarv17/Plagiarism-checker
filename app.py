import os
import uuid
import re
import json
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
PROFILE_FOLDER = os.path.join(app.config['UPLOAD_FOLDER'], 'profiles')
os.makedirs(PROFILE_FOLDER, exist_ok=True)
app.config['PROFILE_FOLDER'] = PROFILE_FOLDER


db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    full_name = db.Column(db.String(100), nullable=True)
    password = db.Column(db.String(200), nullable=False)
    profile_pic = db.Column(db.String(255), nullable=True)
    scans = db.relationship('Scan', backref='user', lazy=True)

class Scan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(150), nullable=False)
    similarity = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    results_json = db.Column(db.Text, nullable=True) # Storing full JSON results

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
    user = User.query.get(session['user_id'])
    from flask import make_response
    response = make_response(render_template('index.html', user=user, username=user.username))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

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
        
        # Save to history
        try:
            new_scan = Scan(
                user_id=session['user_id'],
                filename=file.filename,
                similarity=results.get('similarity', 0),
                results_json=json.dumps(results)
            )
            db.session.add(new_scan)
            db.session.commit()
        except Exception as e:
            print(f"Error saving scan to DB: {e}")
            db.session.rollback()

        try: os.remove(filepath)
        except: pass
        return jsonify(results)

@app.route('/api/history', methods=['GET'])
def get_history():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    scans = Scan.query.filter_by(user_id=session['user_id']).order_by(Scan.timestamp.desc()).all()
    history = [{
        "id": s.id,
        "filename": s.filename,
        "similarity": s.similarity,
        "timestamp": s.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    } for s in scans]
    
    return jsonify(history)

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    scans = Scan.query.filter_by(user_id=session['user_id']).all()
    if not scans:
        return jsonify({"total_scans": 0, "avg_similarity": 0, "high_risk_scans": 0})
    
    total = len(scans)
    avg_sim = sum(s.similarity for s in scans) / total
    high_risk = len([s for s in scans if s.similarity > 40])
    
    # Get last 7 days trends
    return jsonify({
        "total_scans": total,
        "avg_similarity": round(avg_sim, 2),
        "high_risk_scans": high_risk
    })

@app.route('/api/update-profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    new_password = data.get('newPassword')
    email = data.get('email')
    full_name = data.get('fullName')
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({"error": "User not found"}), 404

    if email:
        user.email = email
    if full_name:
        user.full_name = full_name
    if new_password and len(new_password) >= 6:
        user.password = generate_password_hash(new_password)
    
    db.session.commit()
    return jsonify({"message": "Profile updated successfully"})

@app.route('/api/clear-history', methods=['POST'])
def clear_history():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    Scan.query.filter_by(user_id=session['user_id']).delete()
    db.session.commit()
    return jsonify({"message": "History cleared successfully"})

@app.route('/api/upload-avatar', methods=['POST'])
def upload_avatar():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    if 'avatar' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400
    
    file = request.files['avatar']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file:
        user = User.query.get(session['user_id'])
        # Delete old avatar if exists
        if user.profile_pic:
            old_path = os.path.join(app.config['PROFILE_FOLDER'], user.profile_pic)
            if os.path.exists(old_path):
                try: os.remove(old_path)
                except: pass
        
        filename = f"avatar_{user.id}_{uuid.uuid4().hex[:8]}{os.path.splitext(file.filename)[1]}"
        filepath = os.path.join(app.config['PROFILE_FOLDER'], filename)
        file.save(filepath)
        
        user.profile_pic = filename
        db.session.commit()
        
        return jsonify({"message": "Avatar updated", "url": url_for('get_avatar', filename=filename)})

@app.route('/uploads/profiles/<filename>')
def get_avatar(filename):
    return send_file(os.path.join(app.config['PROFILE_FOLDER'], filename))


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

import os

if __name__ == '__main__':
    import socket
    def get_ip():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP

    port = int(os.environ.get("PORT", 10000))
    local_ip = get_ip()
    print(f"\n* Project is accessible on your WiFi network at:")
    print(f"* http://{local_ip}:{port}")
    print(f"* http://localhost:{port}\n")
    
    app.run(host='0.0.0.0', port=port)