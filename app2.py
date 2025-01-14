from flask import Flask, request, jsonify, send_from_directory, render_template, redirect, url_for, session
import os
from flask_sqlalchemy import SQLAlchemy

# Flask uygulaması oluştur
app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Session için gizli anahtar

# SQLite veritabanı konfigürasyonu
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Veritabanı dosyasını burada tanımlıyoruz
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Gereksiz bir özellik, kullanmamıza gerek yok
db = SQLAlchemy(app)  # SQLAlchemy nesnesini oluşturuyoruz

# Yükleme klasörü tanımı
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Kullanıcı veritabanı modeli
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

# Veritabanı tablosunu oluştur
with app.app_context():
    db.create_all()

# Ana sayfa (HTML formu burada)
@app.route('/')
def index():
    if 'username' in session:  # Kullanıcı oturum açmışsa dosya yükleme sayfasını göster
        upload_folder = app.config['UPLOAD_FOLDER']
        files = os.listdir(upload_folder) if os.path.exists(upload_folder) else []
        return render_template('index.html', files=files)  # files değişkenini şablona gönderin
    return redirect(url_for('login'))  # Giriş yapılmamışsa login sayfasına yönlendir

@app.route('/register', methods=['GET', 'POST'])
@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Kullanıcı adı zaten var mı diye kontrol et
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            error = 'Bu kullanıcı adı zaten alındı.'
        else:
            # Yeni kullanıcıyı veritabanına ekle
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))  # Kayıt başarılıysa login sayfasına yönlendir

    return render_template('register.html', error=error)

# Giriş sayfası
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None  

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Veritabanından kullanıcıyı bul
        user = User.query.filter_by(username=username).first()

        if user and user.password == password:
            session['username'] = username  # Kullanıcıyı oturuma kaydet
            return redirect(url_for('index'))
        else:
            error = 'Geçersiz kullanıcı adı veya şifre'  # Set the error message

    return render_template('login.html', error=error)

# Dosya yükleme endpoint'i
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'username' not in session:  # Kullanıcı oturum açmamışsa
        return jsonify({'error': 'Yetkilendirilmemiş işlem'}), 403
    
    if 'file' not in request.files:
        return jsonify({'error': 'Dosya bulunamadı'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Dosya adı boş'}), 400
    
    upload_folder = app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)  # Klasör yoksa oluştur
    file_path = os.path.join(upload_folder, file.filename)
    file.save(file_path)  # Dosyayı kaydet
    return redirect(url_for('index'))

# Yüklenen dosyaların listesini döndürür
@app.route('/files', methods=['GET'])
def list_files():
    if 'username' not in session:  # Yetkilendirme kontrolü
        return jsonify({'error': 'Yetkilendirilmemiş işlem'}), 403

    upload_folder = app.config.get('UPLOAD_FOLDER')
    if not upload_folder or not os.path.exists(upload_folder):
        return jsonify({'error': 'Yükleme klasörü mevcut değil'}), 500

    try:
        # Yüklenen dosyaların listesini al
        files = os.listdir(upload_folder)
        return jsonify(files)
    except Exception as e:
        return jsonify({'error': f'Dosya listesi alınırken hata oluştu: {str(e)}'}), 500


# Belirli bir dosyayı indirir
@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    if 'username' not in session:  # Yetkilendirme kontrolü
        return jsonify({'error': 'Yetkilendirilmemiş işlem'}), 403
    
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Oturumdan çıkış
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# Flask uygulamasını çalıştır
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
