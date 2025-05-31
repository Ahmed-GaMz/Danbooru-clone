from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
import uuid
import base64
import requests

app = Flask(__name__)

# إعدادات الرفع والمجلدات
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# استخدم هنا رابط PostgreSQL من رندر بدل SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://danbooru_db_user:niAnXwCdoulaVIR0fAW8xIfT6RB7zpC1@dpg-d0t5fmk9c44c73954vng-a/danbooru_db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# نموذج قاعدة البيانات للصور
class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(150), nullable=False)
    tags = db.Column(db.String(300), nullable=True)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Image {self.id} - {self.filename}>'

# دالة رفع الصور إلى ImageKit
def upload_to_imagekit(filepath, filename):
    url = "https://upload.imagekit.io/api/v1/files/upload"
    with open(filepath, "rb") as f:
        file_data = f.read()

    private_key = "private_fHM55RpxlyGTdYuoWF3sbPlw1jQ="  # خليك حذر مع المفتاح الخاص!
    auth_header = base64.b64encode(f"{private_key}:".encode()).decode()

    files = {
        "file": (filename, file_data),
        "fileName": (None, filename),
    }

    headers = {
        "Authorization": f"Basic {auth_header}"
    }

    response = requests.post(url, headers=headers, files=files)
    if response.status_code == 200:
        return response.json().get("url")
    else:
        print("فشل رفع الصورة:", response.text)
        return None

# الصفحة الرئيسية
@app.route('/', methods=['GET'])
def index():
    search = request.args.get('search')
    if search:
        images = Image.query.filter(Image.tags.contains(search)).order_by(Image.upload_date.desc()).all()
    else:
        images = Image.query.order_by(Image.upload_date.desc()).all()
    return render_template('index.html', images=images, search=search)

# صفحة رفع الصور
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files.get('file')
        tags = request.form.get('tags', '')

        if not file:
            return "No file uploaded", 400

        if not allowed_file(file.filename):
            return "Invalid file type", 400

        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # رفع إلى ImageKit
        imagekit_url = upload_to_imagekit(filepath, filename)

        # خزن الرابط إذا نجح، أو اسم الملف إذا فشل
        new_image = Image(filename=imagekit_url or filename, tags=tags)
        db.session.add(new_image)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('upload.html')

# صفحة تفاصيل الصورة
@app.route('/image/<int:image_id>')
def image_detail(image_id):
    image = Image.query.get_or_404(image_id)
    tags = image.tags.split(',') if image.tags else []
    return render_template('image_detail.html', image=image, tags=tags)

# السماح بامتدادات الصور فقط
def allowed_file(filename):
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

# لعرض الصور من السيرفر المحلي (إذا مو مرفوعة على ImageKit)
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)