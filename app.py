from flask import Flask, request, render_template, redirect, url_for, session, flash, jsonify, send_from_directory
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta
import time
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
import random
import string
import os
import re
import locale
import smtplib
import urllib.parse
import webbrowser 
from flask_mail import Mail, Message
import jwt


# Koneksi ke database MongoDB
connection_string = "mongodb+srv://test:sparta@cluster0.9kunvma.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(connection_string)
db = client.dbfotografi
users_collection = db.users

app = Flask(__name__)
app.secret_key = 'super-secret-key' 

# Route untuk halaman user
@app.route('/')
def beranda():
    return render_template('user/beranda.html')












# -- Tambahan untuk bagian login, daftar, dkk ---
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'DANANDA34') 
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'KILLING23')
app.config['PASSWORD_RESET_TIMEOUT_MINUTES'] = 30 # Token valid for 30 minutes

# Konfigurasi Upload File
DEFAULT_GCS_PROFILE_PIC_URL = "https://storage.googleapis.com/a1aa/image/10b4ac45-2b8b-450f-888c-bd7182757e8a.jpg"

# --- PERUBAHAN DI SINI ---
UPLOAD_FOLDER = 'gambar_profil_user' # Sesuai dengan folder Anda
# --- AKHIR PERUBAHAN ---
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # Maks 16MB untuk upload

# --- Flask-Mail Configuration ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com' # Contoh: untuk Gmail
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER', 'ovalphotoo@gmail.com') # Email pengirim
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS', 'cvmo ujrb jjpp rsip') # Password email pengirim atau App Password
app.config['MAIL_DEFAULT_SENDER'] = 'ovalphotoo@gmail.com' # Email default pengirim

mail = Mail(app) # Inisialisasi Flask-Mail

# --- Helper Functions ---
def is_valid_email(email):
    """Simple email validation."""
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def allowed_file(filename):
    """Checks if the uploaded file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    """Decorator to protect routes that require user login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({"success": False, "message": "Anda harus login untuk mengakses ini."}), 401
            flash("Anda harus login untuk mengakses halaman ini.", "danger")
            return redirect(url_for('masuk'))
        return f(*args, **kwargs)
    return decorated_function
































# Route untuk halaman admin
@app.route('/admin_dashboard')
def admin_dashboard():
    return render_template('admin/dashboard.html')

# Route untuk halaman pemilik
@app.route('/pemilik_dashboard')
def pemilik_dashboard():
    return render_template('pemilik/dashboard.html')

# Route untuk halaman pemilik
@app.route('/pemilik_pesanan')
def pemilik_pesanan():
    return render_template('pemilik/pesanan.html')

# Route untuk halaman pemilik
@app.route('/pemilik_pendapatan')
def pemilik_pendapatan():
    return render_template('pemilik/pendapatan.html')

@app.route('/pemilik_pengguna')
def pemilik_pengguna():
    return render_template('pemilik/pengguna.html')

@app.route('/pemilik_akunKlien')
def pemilik_akunKlien():
    return render_template('pemilik/akunKlien.html')


def sanitize_filename(name):
    # Ganti spasi dengan underscore dan hapus karakter tidak valid
    name = name.strip().lower()
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[\s-]+', '_', name)
    return name

# Admin - Layanan Fotografi
@app.route('/admin_layananFotografi')
def admin_layananFotografi():
    layanan = list(db.layanan.find())
    return render_template('admin/layananFotografi.html',
layanan=layanan, current_route=request.path)

@app.route("/admin_layananFotografi_toggle/<id>", methods=["POST"])
def admin_layananFotografi_toggle(id):
    data = request.get_json()
    status_baru = bool(data.get("status", True))
    db.layanan.update_one(
        { "_id": ObjectId(id) },
        { "$set": { "status": status_baru } }
    )
    return jsonify({ "ok": True })


@app.route('/admin_layananFotografi_tambah', methods=['GET','POST'])
def admin_layananFotografi_tambah():
    layanan_exists=False
    
    if request.method=='POST':
        nama = request.form['nama']
        gambar = request.files['gambar']
        deskripsi = request.form['deskripsi']

        # Periksa apakah Nama Layanan sudah ada
        existing_layanan = db.layanan.find_one({'nama': nama})
        if existing_layanan:
            layanan_exists = True
        else:
            if gambar and gambar.filename != "":
                ekstensi = os.path.splitext(gambar.filename)[1]
                timestamp = str(int(time.time()))
                nama_file_gambar = f"{sanitize_filename(nama)}_{timestamp}{ekstensi}"
                file_path = os.path.join('static/images/imgLayanan', nama_file_gambar)
                gambar.save(file_path)
            else:
                nama_file_gambar = None
            
            doc = {
                'nama':nama,
                'gambar': nama_file_gambar,
                'deskripsi': deskripsi,
                "status": True   # layanan aktif secara default
            }
            db.layanan.insert_one(doc)
            return redirect(url_for("admin_layananFotografi"))
    return render_template('admin/layananFotografi_tambah.html', layanan_exists=layanan_exists)


@app.route('/check_nama_layanan', methods=['POST'])
def check_nama_layanan():
    data = request.json
    nama_layanan = data.get('nama', '')

    # Periksa apakah nama layanan sudah ada di database MongoDB
    existing_layanan = db.layanan.find_one({'nama': {'$regex': f'^{nama_layanan}$', '$options': 'i'}}) 
    if existing_layanan:
        return jsonify({'exists': True})
    else:
        return jsonify({'exists': False})

@app.route('/admin_layananFotografi_ubah/<_id>', methods=['GET', 'POST'])
def admin_layananFotografi_ubah(_id):
    layanan_exists = False

    if request.method == 'POST':
        id = request.form['_id']
        nama = request.form['nama']
        deskripsi = request.form['deskripsi']
        gambar = request.files['gambar']

        # Periksa apakah Nama Layanan sudah ada, kecuali layanan yang sedang diubah
        existing_layanan = db.layanan.find_one({'nama': nama, '_id': {'$ne': ObjectId(id)}})
        if existing_layanan:
            layanan_exists = True
        else:
            # Ambil data lama untuk akses gambar lama
            old_layanan = db.layanan.find_one({'_id': ObjectId(_id)})
            doc = {
                'nama': nama,
                'deskripsi': deskripsi,
                'status': True,
                'gambar': old_layanan.get('gambar')  # default ke gambar lama
            }

            # Cek apakah user mengunggah file baru
            if gambar and gambar.filename != "":
                ekstensi = os.path.splitext(gambar.filename)[1]
                timestamp = str(int(time.time()))
                nama_file_gambar = f"{sanitize_filename(nama)}_{timestamp}{ekstensi}"
                file_path = os.path.join('static/images/imgLayanan', nama_file_gambar)
                gambar.save(file_path)
                doc['gambar'] = nama_file_gambar

                # Hapus gambar lama
                old_image_filename = old_layanan.get('gambar')
                if old_image_filename and old_image_filename != nama_file_gambar:
                    old_image_path = os.path.join('static/images/imgLayanan', old_image_filename)
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)

            # Update/ubah layanan
            db.layanan.update_one({"_id": ObjectId(_id)}, {"$set": doc})
            return redirect(url_for("admin_layananFotografi"))

    id = ObjectId(_id)
    data = list(db.layanan.find({"_id": id}))
    return render_template('admin/layananFotografi_ubah.html', data=data, layanan_exists=layanan_exists)




@app.route("/katalog_layanan")
def katalog_layanan():
    layanan_list = list(db.layanan.find({ "status": True }))   # hanya layanan aktif

    for layanan in layanan_list:
        # Ambil paket aktif untuk setiap layanan
        paket_list = list(db.paket.find({
            'layanan_id': layanan['_id'],
            'status': True
        }))

        # Format tanggal
        for p in paket_list:
            mulai = p.get('tanggal_mulai')
            selesai = p.get('tanggal_selesai')

            if isinstance(mulai, datetime) and isinstance(selesai, datetime):
                p['tanggal_mulai_formatted'] = tanggal_id(mulai)
                p['tanggal_selesai_formatted'] = tanggal_id(selesai)
            else:
                p['tanggal_mulai_formatted'] = "Tanggal tidak tersedia"
                p['tanggal_selesai_formatted'] = "Tanggal tidak tersedia"

        # Tambahkan paket_list ke dalam data layanan
        layanan['paket_list'] = paket_list

    return render_template(
        "user/katalog_layanan.html",
        layanan=layanan_list,
        current_route=request.path
    )








def tanggal_id(dt: datetime) -> str:
    """
    Ubah datetime ⇢ string "01 Januari 2025".
    Jatuh-bakal ke locale default jika `id_ID` tidak tersedia.
    """
    try:
        locale.setlocale(locale.LC_TIME, "id_ID.UTF-8")
    except locale.Error:
        
        bulan_map = {
            "January": "Januari", "February": "Februari", "March": "Maret",
            "April": "April", "May": "Mei", "June": "Juni",
            "July": "Juli", "August": "Agustus", "September": "September",
            "October": "Oktober", "November": "November", "December": "Desember",
        }
        en = dt.strftime("%d %B %Y")
        for en_bulan, id_bulan in bulan_map.items():
            en = en.replace(en_bulan, id_bulan)
        return en
    return dt.strftime("%d %B %Y")

# Admin - Paket Fotografi
@app.route('/admin_paketFotografi')
def admin_paketFotografi():
    paket = list(db.paket.find())
    layanan_map = {str(l['_id']): l['nama'] for l in db.layanan.find()}

    # Tambahkan nama layanan ke dalam setiap dokumen paket
    for p in paket:
        layanan_id = str(p.get('layanan_id'))
        p['layanan'] = layanan_map.get(layanan_id, 'Tidak ditemukan')

        mulai = p.get('tanggal_mulai')
        selesai = p.get('tanggal_selesai')

        if isinstance(mulai, datetime) and isinstance(selesai, datetime):
            p['tanggal_mulai_formatted'] = tanggal_id(mulai)
            p['tanggal_selesai_formatted'] = tanggal_id(selesai)
        else:
            p['tanggal_mulai_formatted'] = "Tanggal tidak tersedia"
            p['tanggal_selesai_formatted'] = "Tanggal tidak tersedia"


    return render_template('admin/paketFotografi.html', paket=paket, current_route=request.path)

@app.route("/admin_paketFotografi_toggle/<id>", methods=["POST"])
def admin_paketFotografi_toggle(id):
    data = request.get_json()
    status_baru = bool(data.get("status", True))
    db.paket.update_one(
        { "_id": ObjectId(id) },
        { "$set": { "status": status_baru } }
    )
    return jsonify({ "ok": True })


@app.route('/admin_paketFotografi_tambah', methods=['GET','POST'])
def admin_paketFotografi_tambah():
    paket_exists = False

    if request.method == 'POST':
        nama = request.form['nama']
        layanan_id = request.form['layanan']
        harga = int(request.form['harga'])
        deposit = int(request.form['deposit'])
        keuntungan = request.form['keuntungan']
        tim_kerja = request.form['tim_kerja']
        tanggal_mulai_str = request.form['tanggal_mulai']
        tanggal_selesai_str = request.form['tanggal_selesai']

        # Konversi tanggal
        tanggal_mulai = datetime.strptime(tanggal_mulai_str, '%Y-%m-%d')
        tanggal_selesai= datetime.strptime(tanggal_selesai_str, '%Y-%m-%d')

        # Simpan ke dalam dokumen
        doc = {
            'nama': nama,
            'layanan_id': ObjectId(layanan_id),
            'harga': harga,
            'deposit': deposit,
            'keuntungan': keuntungan,
            'tim_kerja': tim_kerja,
            'tanggal_mulai': tanggal_mulai,
            'tanggal_selesai': tanggal_selesai,
            "status": True,
            'created_at': datetime.utcnow()
        }
        db.paket.insert_one(doc)
        return redirect(url_for("admin_paketFotografi"))

    layanan = list(db.layanan.find())
    return render_template('admin/paketFotografi_tambah.html', layanan=layanan, paket_exists=paket_exists)


@app.route('/check_nama_paket', methods=['POST'])
def check_nama_paket():
    data = request.json
    nama_paket = data.get('nama', '')

    # Periksa apakah nama paket sudah ada di database MongoDB
    existing_paket = db.paket.find_one({
        'nama': {'$regex': f'^{nama_paket}$', '$options': 'i'}
    })
    if existing_paket:
        return jsonify({'exists': True})
    else:
        return jsonify({'exists': False})

@app.route('/admin_paketFotografi_ubah/<_id>', methods=['GET', 'POST'])
def admin_paketFotografi_ubah(_id):
    paket_exists = False

    if request.method == 'POST':
        id = request.form['_id']
        nama = request.form['nama']
        layanan_id = request.form['layanan']
        harga = int(request.form['harga'])
        deposit = int(request.form['deposit'])
        keuntungan = request.form['keuntungan']
        tim_kerja = request.form['tim_kerja']
        tanggal_mulai_str = request.form['tanggal_mulai']
        tanggal_selesai_str = request.form['tanggal_selesai']

        tanggal_mulai = datetime.strptime(tanggal_mulai_str, '%Y-%m-%d')
        tanggal_selesai = datetime.strptime(tanggal_selesai_str, '%Y-%m-%d')

         # Periksa apakah Nama paket sudah ada, kecuali paket yang sedang diubah
        existing_paket = db.paket.find_one({'nama': nama, '_id': {'$ne': ObjectId(id)}})
        if existing_paket:
            paket_exists = True
        else:
            doc = {
                'nama': nama,
                'layanan_id': ObjectId(layanan_id),
                'harga': harga,
                'deposit': deposit,
                'keuntungan': keuntungan,
                'tim_kerja': tim_kerja,
                'tanggal_mulai': tanggal_mulai,
                'tanggal_selesai': tanggal_selesai,
                "status": True   # paket aktif secara default
            }

            db.paket.update_one({'_id': ObjectId(_id)}, {'$set': doc})
            return redirect(url_for('admin_paketFotografi'))

    id = ObjectId(_id)
    data = db.paket.find_one({"_id": id})
    layanan = list(db.layanan.find())

    formatted_tanggal_mulai = ""
    formatted_tanggal_selesai = ""

    if data and 'tanggal_mulai' in data and isinstance(data['tanggal_mulai'], datetime):
        formatted_tanggal_mulai = data['tanggal_mulai'].strftime("%Y-%m-%d")

    if data and 'tanggal_selesai' in data and isinstance(data['tanggal_selesai'], datetime):
        formatted_tanggal_selesai = data['tanggal_selesai'].strftime("%Y-%m-%d")


    return render_template('admin/paketFotografi_ubah.html',
                           data=data,
                           layanan=layanan,
                           paket_exists=paket_exists,
                           formatted_tanggal_mulai=formatted_tanggal_mulai,
                           formatted_tanggal_selesai=formatted_tanggal_selesai)



# User - Lihat Paket
@app.route('/lihat_paket/<layanan_id>')
def lihat_paket(layanan_id):
    # Cari layanan berdasarkan id
    layanan = db.layanan.find_one({'_id': ObjectId(layanan_id)})

    # Hanya ambil paket yang aktif
    paket_list = list(db.paket.find({
        'layanan_id': ObjectId(layanan_id),
        'status': True  # hanya paket dengan status aktif
    }))

    for p in paket_list:
        mulai = p.get('tanggal_mulai')
        selesai = p.get('tanggal_selesai')

        if isinstance(mulai, datetime) and isinstance(selesai, datetime):
            p['tanggal_mulai_formatted'] = tanggal_id(mulai)
            p['tanggal_selesai_formatted'] = tanggal_id(selesai)
        else:
            p['tanggal_mulai_formatted'] = "Tanggal tidak tersedia"
            p['tanggal_selesai_formatted'] = "Tanggal tidak tersedia"

    return render_template('user/lihat_paket.html', layanan=layanan, paket_list=paket_list)







# Admin - Galeri
@app.route('/admin_galeri')
def admin_galeri():
    logger = app.logger 
    logger.info("Mengakses route /admin_galeri")
    processed_gallery_items = []
    try:
        gallery_items_cursor = db.galeri.find().sort("tanggal_upload", -1)
        
        for item in gallery_items_cursor:
            nama_layanan_terkait = "-"
            nama_lokasi_terkait = "-"

            if item.get('kategori') == 'layanan' and item.get('id_layanan'):
                try:
                    layanan_obj = db.layanan.find_one({"_id": ObjectId(item['id_layanan'])})
                    if layanan_obj:
                        nama_layanan_terkait = layanan_obj.get('nama', 'N/A')
                except Exception as e:
                    logger.warning(f"Error ObjectId/query layanan untuk galeri {item.get('_id')}: {e}")
            
            elif item.get('kategori') == 'lokasi' and item.get('id_lokasi'):
                try:
                    lokasi_obj = db.lokasi.find_one({"_id": ObjectId(item.get('id_lokasi'))})
                    if lokasi_obj:
                        nama_lokasi_terkait = lokasi_obj.get('nama', 'N/A')
                except Exception as e:
                    logger.warning(f"Error ObjectId/query lokasi untuk galeri {item.get('_id')}: {e}")

            item['nama_layanan_display'] = nama_layanan_terkait
            item['nama_lokasi_display'] = nama_lokasi_terkait
            item['status'] = item.get('status', True) 

            gambar_list = item.get('gambar', [])
            if isinstance(gambar_list, list) and gambar_list:
                item['thumbnail'] = gambar_list[0]
            else:
                item['thumbnail'] = None
                
            processed_gallery_items.append(item)
            
    except Exception as e:
        logger.error(f"Error di route /admin_galeri: {e}", exc_info=True)
        processed_gallery_items = [] 
        flash("Terjadi kesalahan saat mengambil data galeri.", "danger")
        
    return render_template(
        'admin/galeri.html', 
        galeri_items=processed_gallery_items, 
        current_route=request.path
    )

@app.route("/admin_galeri_toggle_status/<item_id>", methods=["POST"])
def admin_galeri_toggle_status(item_id):
    logger = app.logger 
    try:
        data = request.get_json()
        status_baru = bool(data.get("status", False)) 
        
        result = db.galeri.update_one(
            {"_id": ObjectId(item_id)},
            {"$set": {"status": status_baru}}
        )
        
        if result.matched_count == 0:
            return jsonify({"success": False, "message": "Item galeri tidak ditemukan."}), 404
            
        return jsonify({"success": True, "message": "Status galeri berhasil diubah."})
    except Exception as e:
        logger.error(f"Error saat toggle status galeri {item_id}: {e}", exc_info=True)
        return jsonify({"success": False, "message": "Terjadi kesalahan internal."}), 500
    
    

@app.route('/admin_galeri_tambah', methods=['GET', 'POST'])
def admin_galeri_tambah():
    layanan = list(db.layanan.find())
    lokasi = list(db.lokasi.find({"is_active": True})) 

    if request.method == 'POST':
        app.logger.debug(f"Request form data: {request.form}") # Log data form
        app.logger.debug(f"Request files: {request.files}")     # Log file yang diterima

        kategori = request.form.get('kategori')
        layanan_id = request.form.get('layanan')
        lokasi_id = request.form.get('lokasi')
        gambar_files = request.files.getlist('gambar[]')

        app.logger.debug(f"Kategori: {kategori}")
        app.logger.debug(f"Layanan ID: {layanan_id}")
        app.logger.debug(f"Lokasi ID: {lokasi_id}")
        app.logger.debug(f"Jumlah file diterima: {len(gambar_files)}")
        if gambar_files:
            for i, f in enumerate(gambar_files):
                app.logger.debug(f"File {i}: filename='{f.filename}', content_type='{f.content_type}'")


        if not kategori or not gambar_files:
            flash("Kategori dan gambar wajib diisi.", "danger")
            app.logger.warning("Validasi gagal: Kategori atau gambar kosong.")
            return redirect(url_for('admin_galeri_tambah'))

        nama_file_gambar = []
        base_save_path = os.path.join(app.root_path, 'static', 'images', 'imgGaleri') 
        if not os.path.exists(base_save_path):
            try:
                os.makedirs(base_save_path)
                app.logger.info(f"Direktori {base_save_path} dibuat.")
            except OSError as e:
                app.logger.error(f"Gagal membuat direktori {base_save_path}: {e}")
                flash("Terjadi kesalahan server saat membuat direktori penyimpanan.", "danger")
                return redirect(url_for('admin_galeri_tambah'))


        for gambar in gambar_files:
            if gambar and gambar.filename:
                nama_file = secure_filename(gambar.filename)
                simpan_path = os.path.join(base_save_path, nama_file)
                app.logger.debug(f"Mencoba menyimpan file ke: {simpan_path}")
                try:
                    gambar.save(simpan_path)
                    nama_file_gambar.append(nama_file)
                    app.logger.info(f"File {nama_file} berhasil disimpan.")
                except Exception as e:
                    app.logger.error(f"Gagal menyimpan file {nama_file}: {e}")
            else:
                app.logger.warning("Sebuah file dilewati karena tidak valid atau tidak ada filename.")


        if not nama_file_gambar: # Jika tidak ada file yang berhasil disimpan
            flash("Tidak ada file gambar yang berhasil diproses atau disimpan.", "warning")
            return redirect(url_for('admin_galeri_tambah'))

        doc = {
            'kategori': kategori,
            'gambar': nama_file_gambar,
            'id_layanan': ObjectId(layanan_id) if layanan_id else None,
            'id_lokasi': ObjectId(lokasi_id) if lokasi_id else None,
            'tanggal_upload': datetime.now(),
            'status': True
            
        }

        try:
            db.galeri.insert_one(doc)
            app.logger.info(f"Dokumen galeri berhasil disimpan ke DB: {doc.get('_id')}")
            flash("Galeri berhasil ditambahkan!", "success") 
        except Exception as e:
            app.logger.error(f"Gagal menyimpan dokumen ke DB: {e}")
            flash("Gagal menyimpan data galeri ke database.", "danger")
        
            for nf in nama_file_gambar:
                file_to_delete = os.path.join(base_save_path, nf)
                if os.path.exists(file_to_delete):
                    try:
                        os.remove(file_to_delete)
                        app.logger.info(f"File {nf} dihapus karena gagal insert DB.")
                    except OSError as del_err:
                        app.logger.error(f"Gagal menghapus file {nf}: {del_err}")

            return redirect(url_for('admin_galeri_tambah')) 

        return redirect(url_for('admin_galeri'))

    return render_template('admin/galeri_tambah.html',
                           layanan=layanan,
                           lokasi=lokasi,
                           current_route=request.path)


@app.route('/admin_galeri_ubah/<item_id>', methods=['GET', 'POST'])
# @login_required # untuk kalo yang udah login baru bisa ubah
def admin_galeri_ubah(item_id):
    logger = app.logger 
    upload_folder_galeri = os.path.join(app.static_folder, 'images', 'imgGaleri')

    if not os.path.exists(upload_folder_galeri):
        try:
            os.makedirs(upload_folder_galeri)
            logger.info(f"Direktori upload '{upload_folder_galeri}' berhasil dibuat.")
        except OSError as e:
            logger.error(f"Gagal membuat direktori upload '{upload_folder_galeri}': {e}", exc_info=True)
            flash(f"Gagal membuat direktori upload: {e}. Periksa izin folder.", "danger")
            return redirect(url_for('admin_galeri')) 

    try:
        # Cari item galeri berdasarkan ID di database
        gallery_item_to_edit = db.galeri.find_one({'_id': ObjectId(item_id)})
        if not gallery_item_to_edit:
            logger.error(f"Item galeri dengan ID '{item_id}' tidak ditemukan di database.")
            flash("Item galeri tidak ditemukan.", "danger")
            return redirect(url_for('admin_galeri')) 

        if request.method == 'POST':
            logger.info(f"Menerima POST request untuk ubah gambar galeri ID: '{item_id}'")

            deleted_images_filenames = request.form.getlist('deleted_images[]')
            new_image_files = request.files.getlist('gambar_baru[]')

            current_image_list = list(gallery_item_to_edit.get('gambar', []))
            images_after_deletion = [] # List untuk menyimpan gambar yang TIDAK dihapus

            # --- Penghapusan Gambar Lama ---
            for existing_filename in current_image_list:
                if existing_filename in deleted_images_filenames:
                    try:
                        file_path_to_delete = os.path.join(upload_folder_galeri, existing_filename)
                        if os.path.exists(file_path_to_delete):
                            os.remove(file_path_to_delete)
                            logger.info(f"File lama berhasil dihapus dari disk: '{existing_filename}'")
                        else:
                            logger.warning(f"File lama '{existing_filename}' tidak ditemukan di disk saat mencoba menghapus. Mungkin sudah dihapus sebelumnya.")
                    except Exception as e_del:
                        logger.error(f"ERROR: Gagal menghapus file fisik '{existing_filename}': {e_del}", exc_info=True)
                        flash(f"Gagal menghapus beberapa gambar lama: {existing_filename}. Detail: {e_del}", "warning")
                else:
                    images_after_deletion.append(existing_filename) 

            updated_image_list = images_after_deletion 
            newly_saved_filenames = [] # List untuk menyimpan nama file baru yang berhasil disimpan

            # --- Penambahan Gambar Baru ---
            valid_new_files = [f for f in new_image_files if f and f.filename]

            if not valid_new_files:
                logger.info("Tidak ada file gambar baru yang valid yang diunggah.")
            
            for new_file in valid_new_files:
                original_filename = secure_filename(new_file.filename)
                filename_base, file_ext = os.path.splitext(original_filename)

                allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.ico']
                if not file_ext or file_ext.lower() not in allowed_extensions:
                    logger.warning(f"File '{original_filename}' dilewati: Ekstensi tidak valid atau tidak ada ('{file_ext}').")
                    flash(f"File '{original_filename}' dilewati karena ekstensi tidak valid.", "warning")
                    continue 

                unique_filename = f"{filename_base}_{uuid.uuid4().hex[:8]}{file_ext}"
                file_path_to_save = os.path.join(upload_folder_galeri, unique_filename)

                try:
                    logger.debug(f"Mencoba menyimpan file: '{original_filename}' sebagai '{unique_filename}' ke '{file_path_to_save}'")
                    new_file.save(file_path_to_save)
                    newly_saved_filenames.append(unique_filename)
                    logger.info(f"File baru berhasil disimpan ke disk: '{unique_filename}'")
                except Exception as e_save:
                    logger.error(f"ERROR: Gagal menyimpan file baru '{unique_filename}' ke '{file_path_to_save}': {e_save}", exc_info=True)
                    flash(f"Gagal menyimpan file baru '{original_filename}'. Detail: {e_save}. Periksa izin folder.", "danger")
                   

            updated_image_list.extend(newly_saved_filenames)

            # --- Update Dokumen di MongoDB ---
            doc_to_update = {
                'gambar': updated_image_list,
                'tanggal_modifikasi': datetime.now(), 
                'kategori': gallery_item_to_edit.get('kategori'),
                'id_layanan': gallery_item_to_edit.get('id_layanan'),
                'id_lokasi': gallery_item_to_edit.get('id_lokasi'),
                'status': gallery_item_to_edit.get('status', True) 
            }

            db.galeri.update_one({"_id": ObjectId(item_id)}, {"$set": doc_to_update})
            logger.info(f"Item galeri ID '{item_id}' berhasil diupdate di database. Total gambar sekarang: {len(updated_image_list)}.")
            flash("Gambar galeri berhasil diperbarui.", "success")
            
            
            return redirect(url_for('admin_galeri_ubah', item_id=item_id))

        # --- GET request (menampilkan form ubah) ---
        layanan_all_list = list(db.layanan.find({}, {"nama": 1, "_id": 1}))
        lokasi_all_list = list(db.lokasi.find({}, {"nama": 1, "_id": 1}))

        return render_template('admin/galeri_ubah.html',
                                gallery_item=gallery_item_to_edit,
                                layanan_all=layanan_all_list,
                                lokasi_all=lokasi_all_list,
                                current_route=request.path)

    except Exception as e:
        logger.error(f"Terjadi error tak terduga di route /admin_galeri_ubah untuk ID '{item_id}': {e}", exc_info=True)
        flash(f"Terjadi kesalahan saat memproses permintaan ubah galeri: {e}", "danger")
        return redirect(url_for('admin_galeri')) 


@app.route('/galeri')
def galeri():
    """Menampilkan halaman galeri user dengan semua foto aktif secara default."""
    return render_template('user/galeri.html')

@app.route('/api/galeri_data', methods=['GET'])
def get_galeri_data():
    """Endpoint API untuk mengambil data galeri berdasarkan filter."""
    kategori = request.args.get('kategori')
    pilihan_kategori_id = request.args.get('pilihan_kategori')

    app.logger.debug(f"API call received: kategori='{kategori}', pilihan_kategori_id='{pilihan_kategori_id}'")

    query = {"status": True}  # Hanya tampilkan yang aktif

    galeri_items = []
    description_data = {
        "nama_layanan": "-",
        "lokasi": "-",
        "maps": "-",
        "biaya": "-"
    }

    try:
        if kategori and kategori != 'all':
            query['kategori'] = kategori
            if pilihan_kategori_id and pilihan_kategori_id != 'all':
                app.logger.debug(f"Applying specific filter: kategori='{kategori}', ID='{pilihan_kategori_id}'")
                if kategori == 'layanan':
                    try:
                        obj_id = ObjectId(pilihan_kategori_id)
                        query['id_layanan'] = obj_id
                        layanan_obj = db.layanan.find_one({"_id": obj_id})
                        if layanan_obj:
                            description_data["nama_layanan"] = layanan_obj.get('nama', 'N/A')
                            # Mengirim biaya dalam bentuk raw (string/angka) ke frontend
                            description_data["biaya"] = layanan_obj.get('harga', 'N/A') 
                        app.logger.debug(f"Layanan object found: {layanan_obj.get('nama')} with ID {obj_id}")
                    except Exception as e:
                        app.logger.error(f"Error converting layanan_id to ObjectId or finding layanan: {e}", exc_info=True)
                        description_data = { "nama_layanan": "-", "lokasi": "-", "maps": "-", "biaya": "-" }
                        galeri_items = []
                        return jsonify({"gallery_items": galeri_items, "description_data": description_data})
                elif kategori == 'lokasi':
                    try:
                        obj_id = ObjectId(pilihan_kategori_id)
                        query['id_lokasi'] = obj_id
                        lokasi_obj = db.lokasi.find_one({"_id": obj_id})
                        if lokasi_obj:
                            description_data["nama_layanan"] = "Galeri Lokasi"
                            description_data["lokasi"] = lokasi_obj.get('nama', 'N/A')
                            description_data["maps"] = lokasi_obj.get('link_maps', 'N/A') 
                            # Mengirim biaya dalam bentuk raw (string/angka) ke frontend
                            description_data["biaya"] = lokasi_obj.get('biaya', 'N/A') 
                        app.logger.debug(f"Lokasi object found: {lokasi_obj.get('nama')} with ID {obj_id}")
                    except Exception as e:
                        app.logger.error(f"Error converting lokasi_id to ObjectId or finding lokasi: {e}", exc_info=True)
                        description_data = { "nama_layanan": "-", "lokasi": "-", "maps": "-", "biaya": "-" }
                        galeri_items = []
                        return jsonify({"gallery_items": galeri_items, "description_data": description_data})
            else:
                query.pop('id_layanan', None)
                query.pop('id_lokasi', None)
                description_data = { "nama_layanan": "-", "lokasi": "-", "maps": "-", "biaya": "-" }
                app.logger.debug(f"Kategori selected, but specific choice is 'all'. Query: {query}")
        else:
            description_data = { "nama_layanan": "-", "lokasi": "-", "maps": "-", "biaya": "-" }
            app.logger.debug(f"Kategori 'all' selected. Query: {query}")

        app.logger.debug(f"Final MongoDB Query for galeri: {query}")
        cursor = db.galeri.find(query)
        
        if db.galeri.count_documents(query) == 0:
            app.logger.warning(f"No gallery items found for query: {query}")
        
        for item in cursor:
            if isinstance(item.get('gambar'), list) and item['gambar']:
                item['_id'] = str(item['_id'])
                if item.get('id_layanan'):
                    item['id_layanan'] = str(item['id_layanan'])
                if item.get('id_lokasi'):
                    item['id_lokasi'] = str(item['id_lokasi'])
                
                galeri_items.append(item)
        app.logger.debug(f"Number of gallery items returned: {len(galeri_items)}")
        
    except Exception as e:
        app.logger.error(f"Error saat mengambil data galeri: {e}", exc_info=True) 
        return jsonify({"error": "Terjadi kesalahan saat mengambil data galeri."}), 500

    return jsonify({
        "gallery_items": galeri_items,
        "description_data": description_data
    })

@app.route('/api/kategori_options', methods=['GET'])
def get_kategori_options():
    """Endpoint API untuk mengambil opsi kategori dan pilihan kategori."""
    data = {
        "kategori": [
            {"value": "all", "text": "Semua Kategori"},
            {"value": "layanan", "text": "Layanan"},
            {"value": "lokasi", "text": "Lokasi"}
        ],
        "pilihan_kategori": {
            "layanan": [{"value": "all", "text": "Semua Layanan"}],
            "lokasi": [{"value": "all", "text": "Semua Lokasi"}]
        }
    }

    try:
        layanan_cursor = db.layanan.find({"status": True}, {"_id": 1, "nama": 1}) 
        for layanan in layanan_cursor:
            data["pilihan_kategori"]["layanan"].append({
                "value": str(layanan['_id']),
                "text": layanan['nama']
            })

        lokasi_cursor = db.lokasi.find({"is_active": True}, {"_id": 1, "nama": 1}) 
        for lokasi in lokasi_cursor:
            data["pilihan_kategori"]["lokasi"].append({
                "value": str(lokasi['_id']),
                "text": lokasi['nama']
            })

    except Exception as e:
        app.logger.error(f"Error saat mengambil opsi kategori: {e}", exc_info=True) 
        return jsonify({"error": "Terjadi kesalahan saat mengambil opsi kategori."}), 500

    return jsonify(data)






# Admin - Lokasi
@app.route('/admin_lokasi')
def admin_lokasi():
    lokasi = list(db.lokasi.find())
    return render_template('admin/lokasi.html', lokasi=lokasi, current_route=request.path)

@app.route('/admin_lokasi_tambah', methods=['GET', 'POST'])
def admin_lokasi_tambah():
    lokasi_exists = False

    if request.method == 'POST':
        nama = request.form['nama']
        alamat = request.form['alamat']
        link_maps = request.form['link_maps']
        biaya = int(request.form['biaya'])  

        # Periksa apakah Nama Lokasi sudah ada
        existing_lokasi = db.lokasi.find_one({'nama': nama})
        if existing_lokasi:
            lokasi_exists = True
        else:
            doc = {
                'nama': nama,
                'alamat': alamat,
                'link_maps': link_maps,
                'biaya': biaya,
                'is_active': True
            }
            db.lokasi.insert_one(doc)
            return redirect(url_for("admin_lokasi"))

    return render_template('admin/lokasi_tambah.html', lokasi_exists=lokasi_exists)


@app.route('/check_nama_lokasi', methods=['POST'])
def check_nama_lokasi():
    data = request.json
    nama_lokasi = data.get('nama', '')

    # Periksa apakah nama lokasi sudah ada di database MongoDB
    existing_lokasi = db.lokasi.find_one({'nama': {'$regex': f'^{nama_lokasi}$', '$options': 'i'}})
    if existing_lokasi:
        return jsonify({'exists': True})
    else:
        return jsonify({'exists': False})


@app.route('/admin_lokasi_ubah/<id>', methods=['GET', 'POST'])
def admin_lokasi_ubah(id):
    """
    Menampilkan form ubah lokasi dan menangani update data.
    """
    try:
        lokasi_id = ObjectId(id)
    except:
        return redirect(url_for('admin_lokasi')) # Redirect if ID is invalid

    lokasi = db.lokasi.find_one({'_id': lokasi_id})

    if not lokasi:
        return redirect(url_for('admin_lokasi')) # Redirect if location not found

    if request.method == 'POST':
        new_nama = request.form['nama'].strip()
        new_alamat = request.form['alamat'].strip()
        new_link_maps = request.form['link_maps'].strip()
        new_biaya = int(request.form['biaya'])

        # Check for duplicate name, excluding the current location being edited
        existing_lokasi = db.lokasi.find_one({
            'nama': {'$regex': f'^{new_nama}$', '$options': 'i'},
            '_id': {'$ne': lokasi_id} # Exclude current document
        })

        if existing_lokasi:
            # You might want to flash a message here or handle it differently
            # For now, let's re-render the form with an error.
            return render_template('admin/lokasi_ubah.html', lokasi=lokasi, name_exists_error=True)
        else:
            db.lokasi.update_one(
                {'_id': lokasi_id},
                {'$set': {
                    'nama': new_nama,
                    'alamat': new_alamat,
                    'link_maps': new_link_maps,
                    'biaya': new_biaya
                }}
            )
            return redirect(url_for("admin_lokasi"))

    return render_template('admin/lokasi_ubah.html', lokasi=lokasi, current_route=request.path)

@app.route('/toggle_lokasi_status/<id>', methods=['POST'])
def toggle_lokasi_status(id):
    """
    Mengubah status aktif/nonaktif lokasi.
    """
    try:
        lokasi_id = ObjectId(id)
    except:
        return jsonify({'success': False, 'message': 'Invalid ID'}), 400

    lokasi = db.lokasi.find_one({'_id': lokasi_id})

    if not lokasi:
        return jsonify({'success': False, 'message': 'Location not found'}), 404

    current_status = lokasi.get('is_active', False)
    new_status = not current_status

    db.lokasi.update_one(
        {'_id': lokasi_id},
        {'$set': {'is_active': new_status}}
    )
    return jsonify({'success': True, 'new_status': new_status})






# Admin - Jadwal (Menampilkan semua jadwal)
@app.route('/admin_jadwal')
def admin_jadwal():
    all_pesanan_list = []
    try:
        # Ambil semua pesanan dari database
        pesanan_cursor = db.pesanan.find().sort('created_at', -1) # Urutkan dari yang terbaru

        # Buat map nama layanan, paket, dan lokasi berdasarkan _id
        layanan_map = {str(l['_id']): l['nama'] for l in db.layanan.find()}
        paket_map = {str(l['_id']): l['nama'] for l in db.paket.find()}
        lokasi_map = {str(l['_id']): l['nama'] for l in db.lokasi.find()}

        for pesanan in pesanan_cursor:
            # Konversi ObjectId pesanan ke string
            pesanan['_id'] = str(pesanan['_id'])

            # Layanan
            layanan_id = str(pesanan.get('layanan_id', ''))
            pesanan['layanan'] = layanan_map.get(layanan_id, 'Tidak ditemukan')

            # Paket
            paket_id = str(pesanan.get('paket_id', ''))
            pesanan['paket'] = paket_map.get(paket_id, 'Tidak ditemukan')

            # Lokasi (bisa None atau kosong jika input manual)
            lokasi_id = str(pesanan.get('lokasi_id', ''))
            if lokasi_id and lokasi_id != "None":
                pesanan['lokasi'] = lokasi_map.get(lokasi_id, 'Tidak ditemukan')
            else:
                pesanan['lokasi'] = 'Lokasi pilihan sendiri' if pesanan.get('alamat_lokasi_acara') else 'Tidak tersedia'

            # Format tanggal
            if isinstance(pesanan.get('tanggal_mulai_acara'), datetime):
                pesanan['tanggal_mulai_acara_formatted'] = tanggal_id(pesanan['tanggal_mulai_acara'])
            else:
                pesanan['tanggal_mulai_acara_formatted'] = 'N/A' # Fallback for missing or invalid date
            if isinstance(pesanan.get('tanggal_selesai_acara'), datetime):
                pesanan['tanggal_selesai_acara_formatted'] = tanggal_id(pesanan['tanggal_selesai_acara'])
            else:
                pesanan['tanggal_selesai_acara_formatted'] = 'N/A' # Fallback for missing or invalid date

            all_pesanan_list.append(pesanan)

        return render_template('admin/jadwal.html', pesanan=all_pesanan_list, current_route=request.path)

    except Exception as e:
        flash(f"Terjadi kesalahan saat mengambil data jadwal: {e}", "danger")
        # Jika terjadi kesalahan, Anda bisa me-render template dengan daftar kosong
        # atau redirect ke halaman dashboard admin.
        return render_template('admin/jadwal.html', pesanan=[], current_route=request.path)



@app.route('/admin_jadwal_ubah/<_id>', methods=['GET', 'POST'])
def admin_jadwal_ubah(_id):
    return render_template('admin/jadwal_ubah.html')








# Pesanan
# --- Routes API untuk Frontend ---

@app.route('/api/all_paket', methods=['GET'])
def api_all_paket():
    """Mengembalikan semua data paket, termasuk harga dan deposit."""
    paket_data = list(db.paket.find({'status': True}))
    for paket in paket_data:
        if '_id' in paket:
            paket['_id'] = str(paket['_id'])
        if 'layanan_id' in paket:
            paket['layanan_id'] = str(paket['layanan_id'])
        
        if 'deposit' not in paket or not isinstance(paket['deposit'], (int, float)):
            paket['deposit'] = 0
        
        if 'harga' not in paket or not isinstance(paket['harga'], (int, float)):
            paket['harga'] = 0
    return jsonify(paket_data)

@app.route('/api/all_lokasi', methods=['GET'])
def api_all_lokasi():
    """Mengembalikan semua data lokasi, termasuk biaya."""
    lokasi_data = list(db.lokasi.find({'is_active': True}))
    for lokasi in lokasi_data:
        if '_id' in lokasi:
            lokasi['_id'] = str(lokasi['_id'])
        
        if 'biaya' not in lokasi or not isinstance(lokasi['biaya'], (int, float)):
            lokasi['biaya'] = 0
    return jsonify(lokasi_data)


# Admin - Pesanan
@app.route('/admin_pesanan')
def admin_pesanan():
    pesanan = list(db.pesanan.find().sort('created_at', -1))
    layanan_map = {str(l['_id']): l['nama'] for l in db.layanan.find()}

    # Tambahkan nama layanan ke dalam setiap dokumen pesanan
    for p in pesanan:
        layanan_id = str(p.get('layanan_id'))
        p['layanan'] = layanan_map.get(layanan_id, 'Tidak ditemukan')
       

        if isinstance(p.get('tanggal_mulai_acara'), datetime):
            p['tanggal_mulai_acara_formatted'] = tanggal_id(p['tanggal_mulai_acara'])
        if isinstance(p.get('tanggal_selesai_acara'), datetime):
            p['tanggal_selesai_acara_formatted'] = tanggal_id(p['tanggal_selesai_acara'])
    return render_template('admin/pesanan.html', pesanan=pesanan, current_route=request.path)

UPLOAD_FOLDER_SURAT_IZIN = 'static/suratIzin'
if not os.path.exists(UPLOAD_FOLDER_SURAT_IZIN):
    os.makedirs(UPLOAD_FOLDER_SURAT_IZIN)
app.config['UPLOAD_FOLDER_SURAT_IZIN'] = UPLOAD_FOLDER_SURAT_IZIN

ADDITIONAL_DAY_COST_PER_DAY = 500000


@app.route('/admin_pesanan_tambah', methods=['GET', 'POST'])
def admin_pesanan_tambah():
    if request.method == 'POST':
        try:
            # Mengambil data dari form
            tanggal_pemesanan_str = request.form['tanggal_pemesanan']
            layanan_id = request.form['layanan_id'] # From hidden input
            paket_id = request.form['paket_id']     # From hidden input
            nama_klien = request.form['nama_klien']
            nama_orang_tua = request.form['nama_orang_tua']
            telepon_orang_tua = request.form['telepon_orang_tua']
            email_klien = request.form['email_klien']
            telepon_klien = request.form['telepon_klien']
            whatsapp_klien = request.form['whatsapp_klien']
            instagram_klien = request.form.get('instagram_klien', '')
            facebook_klien = request.form.get('facebook_klien', '')

            jam_acara_str = request.form['jam_acara']
            tanggal_mulai_acara_str = request.form['tanggal_mulai_acara']
            tanggal_selesai_acara_str = request.form['tanggal_selesai_acara']

            lokasi_luar_str = request.form['lokasi_luar']
            lokasi_luar = True if lokasi_luar_str == 'iya' else False

            lokasi_pilihan_user = request.form.get('lokasi_id')

            alamat_lokasi_manual = request.form.get('alamat_lokasi_manual', '')
            link_maps_manual = request.form.get('link_maps_manual', '')

            biaya_transportasi_str = request.form.get('biaya_transportasi', '0')
            # Sanitize input: remove non-numeric chars except the dot for float conversion
            # Then convert to int (assuming integer prices for now)
            biaya_transportasi = int(biaya_transportasi_str.replace('.', '').replace(',', '')) if biaya_transportasi_str.replace('.', '').replace(',', '').isdigit() else 0


            # Konversi tanggal dan waktu
            tanggal_pemesanan = datetime.strptime(tanggal_pemesanan_str, '%Y-%m-%d')
            jam_acara = jam_acara_str
            tanggal_mulai_acara = datetime.strptime(tanggal_mulai_acara_str, '%Y-%m-%d')
            tanggal_selesai_acara = datetime.strptime(tanggal_selesai_acara_str, '%Y-%m-%d')

            # Get harga paket dan deposit dari form (hidden fields)
            # This is important: Use the values sent from the form, which were derived from the DB
            harga_paket = float(request.form.get('harga_paket_dasar', '0'))
            deposit_paket = float(request.form.get('deposit_paket_dasar', '0'))

            # Calculate Biaya Tambah Hari
            diff_days = (tanggal_selesai_acara - tanggal_mulai_acara).days
            biaya_tambahan_hari = 0
            if diff_days > 0: # Only charge for additional days beyond the first
                biaya_tambahan_hari = diff_days * ADDITIONAL_DAY_COST_PER_DAY

            # Determine Lokasi details and cost
            biaya_lokasi = 0
            alamat_lokasi_final = None
            link_maps_final = None
            lokasi_id_db = None

            if lokasi_pilihan_user == "pilih_lokasi_sendiri":
                biaya_lokasi = 0 # No additional cost for custom location
                alamat_lokasi_final = alamat_lokasi_manual
                link_maps_final = link_maps_manual
            elif lokasi_pilihan_user:
                selected_lokasi = db.lokasi.find_one({'_id': ObjectId(lokasi_pilihan_user)})
                if selected_lokasi:
                    biaya_lokasi = selected_lokasi.get('biaya', 0)
                    alamat_lokasi_final = selected_lokasi.get('alamat')
                    link_maps_final = selected_lokasi.get('link_maps')
                    lokasi_id_db = ObjectId(lokasi_pilihan_user)
            else: # If no location is selected (e.g., optional field but client left it blank)
                biaya_lokasi = 0
                alamat_lokasi_final = ""
                link_maps_final = ""

            # Recalculate Total Harga and Sisa Bayar on backend
            # Use the harga_paket and deposit_paket obtained from the form's hidden fields
            recalculated_total_harga = harga_paket + biaya_tambahan_hari + biaya_lokasi + biaya_transportasi
            recalculated_sisa_bayar = recalculated_total_harga - deposit_paket

            # Handle upload Surat Izin Lokasi (Opsional)
            surat_izin_lokasi_filename = None
            if 'surat_izin_lokasi' in request.files:
                surat_izin_file = request.files['surat_izin_lokasi']
                if surat_izin_file and surat_izin_file.filename != '':
                    filename_ext = os.path.splitext(surat_izin_file.filename)
                    # Use sanitized client name for filename
                    unique_filename = f"{sanitize_filename(nama_klien)}_surat_izin_{int(time.time())}{filename_ext[1]}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER_SURAT_IZIN'], unique_filename)
                    surat_izin_file.save(file_path)
                    surat_izin_lokasi_filename = unique_filename

            # Buat dokumen pesanan
            pesanan_doc = {
                'tanggal_pemesanan': tanggal_pemesanan, # Store as datetime object
                'layanan_id': ObjectId(layanan_id),
                'paket_id': ObjectId(paket_id),
                'nama_klien': nama_klien,
                'nama_orang_tua': nama_orang_tua,
                'telepon_orang_tua': telepon_orang_tua,
                'email_klien': email_klien,
                'telepon_klien': telepon_klien,
                'whatsapp_klien': whatsapp_klien,
                'instagram_klien': instagram_klien,
                'facebook_klien': facebook_klien,
                'jam_acara': jam_acara,
                'tanggal_mulai_acara': tanggal_mulai_acara, # Store as datetime object
                'tanggal_selesai_acara': tanggal_selesai_acara, # Store as datetime object
                'lokasi_luar_labuhanbatu': lokasi_luar,
                'lokasi_id': lokasi_id_db,
                'alamat_lokasi_acara': alamat_lokasi_final,
                'link_maps_acara': link_maps_final,
                'surat_izin_lokasi': surat_izin_lokasi_filename,
                'biaya_transportasi_akomodasi': biaya_transportasi,
                'biaya_tambahan_hari': biaya_tambahan_hari,
                'biaya_lokasi': biaya_lokasi,
                'harga_paket': harga_paket, # Store base package price from form
                'deposit': deposit_paket,   # Store base deposit from form
                'total_harga': recalculated_total_harga, # Store calculated total
                'sisa_bayar': recalculated_sisa_bayar,   # Store calculated remaining payment
                'status_pesanan': 'Menunggu Konfirmasi',
                'created_at': datetime.utcnow()
            }

            db.pesanan.insert_one(pesanan_doc)
            flash("Pesanan berhasil dibuat!", "success")
            return redirect(url_for("admin_pesanan")) # Redirect to admin pesanan list after successful booking

        except Exception as e:
            print(f"Error adding order: {e}")
            flash(f"Terjadi kesalahan saat menambahkan pesanan: {e}", "danger")
            # If there's an error, re-render the form with existing data if possible
            layanan_list = list(db.layanan.find({'status': True}))
            lokasi_list = list(db.lokasi.find({'is_active': True}))
            for layanan in layanan_list:
                layanan['_id'] = str(layanan['_id'])
            for lokasi in lokasi_list:
                lokasi['_id'] = str(lokasi['_id'])
            return render_template('user/booking.html',
                                   layanan_list=layanan_list, 
                                   lokasi_list=lokasi_list,
                                   error_message=f"Terjadi kesalahan: {e}",
                                   selected_paket_id=request.form.get('paket_id'),
                                   selected_layanan_id=request.form.get('layanan_id'),
                                   selected_paket_nama=request.form.get('paket_nama'), 
                                   selected_paket_harga_raw=float(request.form.get('harga_paket_dasar', '0')),
                                   selected_paket_deposit_raw=float(request.form.get('deposit_paket_dasar', '0'))
                                   )

   
    layanan_list = list(db.layanan.find({'status': True}))
    lokasi_list = list(db.lokasi.find({'is_active': True}))
    for layanan in layanan_list:
        layanan['_id'] = str(layanan['_id'])
    for lokasi in lokasi_list:
        lokasi['_id'] = str(lokasi['_id'])
    return render_template('admin/pesanan_tambah.html',
                           layanan_list=layanan_list,
                           lokasi_list=lokasi_list)

@app.route('/admin_pesanan_detail')
def admin_pesanan_detail():
    pesanan_id = request.args.get('pesanan_id')

    # Tambahkan pengecekan ini
    if not pesanan_id:
        flash("ID Pesanan tidak ditemukan.", "danger")
        return redirect(url_for('admin_pesanan'))

    try:
        pesanan = db.pesanan.find_one({'_id': ObjectId(pesanan_id)})

        # Pengecekan jika pesanan tidak ditemukan di database
        if not pesanan:
            flash(f"Pesanan dengan ID '{pesanan_id}' tidak ditemukan.", "danger")
            return redirect(url_for('admin_pesanan'))

        # Buat map nama layanan, paket, dan lokasi berdasarkan _id
        layanan_map = {str(l['_id']): l['nama'] for l in db.layanan.find()}
        paket_map = {str(l['_id']): l['nama'] for l in db.paket.find()}
        lokasi_map = {str(l['_id']): l['nama'] for l in db.lokasi.find()}

        # Konversi ObjectId pesanan ke string untuk digunakan di URL/form
        pesanan['_id'] = str(pesanan['_id'])

        # Layanan
        layanan_id = str(pesanan.get('layanan_id', ''))
        pesanan['layanan'] = layanan_map.get(layanan_id, 'Tidak ditemukan')

        # Paket
        paket_id = str(pesanan.get('paket_id', ''))
        pesanan['paket'] = paket_map.get(paket_id, 'Tidak ditemukan')

        # Lokasi (bisa None atau kosong jika input manual)
        lokasi_id = str(pesanan.get('lokasi_id', ''))
        if lokasi_id and lokasi_id != "None":
            pesanan['lokasi'] = lokasi_map.get(lokasi_id, 'Tidak ditemukan')
        else:
            pesanan['lokasi'] = 'Lokasi pilihan sendiri' if pesanan.get('alamat_lokasi_acara') else 'Tidak tersedia'

        # Format tanggal
        if isinstance(pesanan.get('tanggal_pemesanan'), datetime):
            pesanan['tanggal_pemesanan_formatted'] = tanggal_id(pesanan['tanggal_pemesanan'])
        if isinstance(pesanan.get('tanggal_mulai_acara'), datetime):
            pesanan['tanggal_mulai_acara_formatted'] = tanggal_id(pesanan['tanggal_mulai_acara'])
        if isinstance(pesanan.get('tanggal_selesai_acara'), datetime):
            pesanan['tanggal_selesai_acara_formatted'] = tanggal_id(pesanan['tanggal_selesai_acara'])

        return render_template('admin/pesanan_detail.html', pesanan=[pesanan], current_route=request.path)

    except Exception as e:
        flash(f"Terjadi kesalahan saat mengambil detail pesanan: {e}", "danger")
        return redirect(url_for('admin_pesanan'))


@app.route('/admin_pesanan_update/<pesanan_id>', methods=['POST'])
def admin_pesanan_update(pesanan_id):
    status = request.form.get('status_pesanan')
    catatan = request.form.get('catatan')
    link_drive = request.form.get('link_google_drive')
    biaya_transportasi_str = request.form.get('biaya_transportasi', '0').replace('.', '').replace(',', '')
    try:
        biaya_transportasi = int(biaya_transportasi_str)
    except ValueError:
        biaya_transportasi = 0

    update_data = {}
    if status is not None:
        update_data['status_pesanan'] = status
    if catatan is not None:
        update_data['catatan'] = catatan
    if link_drive is not None:
        update_data['link_google_drive'] = link_drive
    if biaya_transportasi is not None:
        update_data['biaya_transportasi_akomodasi'] = biaya_transportasi

    try:
        db.pesanan.update_one({'_id': ObjectId(pesanan_id)}, {'$set': update_data})
        flash("Data pesanan berhasil diperbarui!", "success")
    except Exception as e:
        flash(f"Gagal memperbarui data pesanan: {e}", "danger")

    return redirect(url_for('admin_pesanan'))





def kirim_email_pengingat(to, subject, body):
    try:
        msg = Message(subject, recipients=[to])
        msg.body = body
        mail.send(msg)
        print(f"[SUKSES] Email terkirim ke {to}")
    except Exception as e:
        print(f"[ERROR] Gagal kirim email ke {to} | Error: {e}")

@app.route('/admin_kirim_pengingat', methods=['POST'])
def admin_kirim_pengingat():
    email = request.form['email_klien']
    status = request.form['status_pesanan']
    nama = request.form['nama_klien']
    pesanan_id_for_redirect = request.form.get('pesanan_id_for_redirect')

    # Format isi pesan
    if status == 'Belum Pemotretan':
        pesan = f"Halo {nama}, ini adalah pengingat untuk jadwal pemotretan Anda bersama Oval Photo."
    elif status == 'Sudah Pemotretan':
        pesan = f"Halo {nama}, mohon melakukan pelunasan pembayaran untuk layanan fotografi Oval Photo."
    elif status == 'Sudah Kirim File & Album':
        pesan = f"Halo {nama}, semoga Anda puas. Silakan beri ulasan mengenai layanan kami di Oval Photo :)"
    else:
        pesan = f"Halo {nama}, status pesanan Anda saat ini: {status}. Tidak ada pengingat spesifik."

    # Kirim email resmi
    kirim_email_pengingat(email, "Pengingat dari Oval Photo", pesan)

    flash("Pengingat berhasil dikirim melalui Email resmi", "success")

    if pesanan_id_for_redirect:
        return redirect(url_for('admin_pesanan', pesanan_id=pesanan_id_for_redirect))
    else:
        return redirect(url_for('admin_pesanan'))

# User - Pemesanan (GET request - tampilan form)
@app.route('/booking', methods=['GET'])
def booking():
    paket_id = request.args.get('paket_id')

    selected_paket_id = None
    selected_layanan_id = None
    selected_paket_nama = None
    selected_paket_harga_formatted = None
    selected_paket_deposit_formatted = None
    selected_paket_harga_raw = 0
    selected_paket_deposit_raw = 0

    lokasi_list = list(db.lokasi.find({'is_active': True}))
    for lokasi in lokasi_list:
        lokasi['_id'] = str(lokasi['_id'])

    if paket_id:
        try:
            paket_data = db.paket.find_one({'_id': ObjectId(paket_id)})
            if paket_data:
                selected_paket_id = str(paket_data['_id'])
                selected_paket_nama = paket_data.get('nama')
                harga = paket_data.get('harga')
                deposit = paket_data.get('deposit')
                layanan_id = paket_data.get('layanan_id')

                if layanan_id:
                    selected_layanan_id = str(layanan_id)

                if harga is not None:
                    selected_paket_harga_raw = float(harga)
                    selected_paket_harga_formatted = "{:,.0f}".format(selected_paket_harga_raw).replace(',', '.')
                if deposit is not None:
                    selected_paket_deposit_raw = float(deposit)
                    selected_paket_deposit_formatted = "{:,.0f}".format(selected_paket_deposit_raw).replace(',', '.')
            else:
                flash(f"Paket dengan ID '{paket_id}' tidak ditemukan.", "danger")
                return redirect(url_for('katalog_layanan')) # Redirect if package not found
        except Exception as e:
            print(f"Error fetching package data: {e}")
            flash("Terjadi kesalahan saat memuat detail paket.", "danger")
            return redirect(url_for('katalog_layanan')) # Or wherever appropriate

    return render_template('user/booking.html',
                           selected_paket_id=selected_paket_id,
                           selected_layanan_id=selected_layanan_id,
                           selected_paket_nama=selected_paket_nama,
                           selected_paket_harga=selected_paket_harga_formatted,
                           selected_paket_deposit=selected_paket_deposit_formatted,
                           selected_paket_harga_raw=selected_paket_harga_raw,
                           selected_paket_deposit_raw=selected_paket_deposit_raw,
                           lokasi_list=lokasi_list)


# User - Pemesanan (POST request - submit form)
@app.route('/booking', methods=['POST'])
@login_required
def submit_booking():
    try:
        tanggal_pemesanan = request.form['tanggal_pemesanan']
        layanan_id = request.form['layanan_id'] # From hidden input
        paket_id = request.form['paket_id']      # From hidden input
        nama_klien = request.form['nama_klien']
        nama_orang_tua = request.form['nama_orang_tua']
        telepon_orang_tua = request.form['telepon_orang_tua']
        email_klien = request.form['email_klien']
        telepon_klien = request.form['telepon_klien']
        whatsapp_klien = request.form['whatsapp_klien']
        instagram_klien = request.form.get('instagram_klien', '')
        facebook_klien = request.form.get('facebook_klien', '')

        jam_acara_str = request.form['jam_acara']
        tanggal_mulai_acara_str = request.form['tanggal_mulai_acara']
        tanggal_selesai_acara_str = request.form['tanggal_selesai_acara']

        lokasi_luar_str = request.form['lokasi_luar']
        lokasi_luar = True if lokasi_luar_str == 'iya' else False

        lokasi_pilihan_user = request.form.get('lokasi_id')

        alamat_lokasi_manual = request.form.get('alamat_lokasi_manual', '')
        link_maps_manual = request.form.get('link_maps_manual', '')

        biaya_transportasi = float(request.form.get('biaya_transportasi', '0'))

        # Konversi tanggal dan waktu
        jam_acara = jam_acara_str
        tanggal_mulai_acara = datetime.strptime(tanggal_mulai_acara_str, '%Y-%m-%d')
        tanggal_selesai_acara = datetime.strptime(tanggal_selesai_acara_str, '%Y-%m-%d')

        # Get harga paket dan deposit dari form (hidden fields)
        harga_paket = float(request.form.get('harga_paket_dasar', '0'))
        deposit_paket = float(request.form.get('deposit_paket_dasar', '0'))

        # Calculate Biaya Tambah Hari
        diff_days = (tanggal_selesai_acara - tanggal_mulai_acara).days
        biaya_tambahan_hari = 0
        if diff_days > 0: # Only charge for additional days beyond the first
            biaya_tambahan_hari = diff_days * ADDITIONAL_DAY_COST_PER_DAY

        # Determine Lokasi details and cost
        biaya_lokasi = 0
        alamat_lokasi_final = None
        link_maps_final = None
        lokasi_id_db = None

        if lokasi_pilihan_user == "pilih_lokasi_sendiri":
            biaya_lokasi = 0 # No additional cost for custom location
            alamat_lokasi_final = alamat_lokasi_manual
            link_maps_final = link_maps_manual
        elif lokasi_pilihan_user:
            selected_lokasi = db.lokasi.find_one({'_id': ObjectId(lokasi_pilihan_user)})
            if selected_lokasi:
                biaya_lokasi = selected_lokasi.get('biaya', 0)
                alamat_lokasi_final = selected_lokasi.get('alamat')
                link_maps_final = selected_lokasi.get('link_maps')
                lokasi_id_db = ObjectId(lokasi_pilihan_user)
        else: # If no location is selected (e.g., optional field but client left it blank)
            biaya_lokasi = 0
            alamat_lokasi_final = ""
            link_maps_final = ""

        # Recalculate Total Harga and Sisa Bayar on backend
        recalculated_total_harga = harga_paket + biaya_tambahan_hari + biaya_lokasi + biaya_transportasi
        recalculated_sisa_bayar = recalculated_total_harga - deposit_paket

        # Handle upload Surat Izin Lokasi (Opsional)
        surat_izin_lokasi_filename = None
        if 'surat_izin_lokasi' in request.files:
            surat_izin_file = request.files['surat_izin_lokasi']
            if surat_izin_file and surat_izin_file.filename != '':
                filename_ext = os.path.splitext(surat_izin_file.filename)
                # Use sanitized client name for filename
                unique_filename = f"{sanitize_filename(nama_klien)}_surat_izin_{int(time.time())}{filename_ext[1]}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER_SURAT_IZIN'], unique_filename)
                surat_izin_file.save(file_path)
                surat_izin_lokasi_filename = unique_filename

        # Buat dokumen pesanan
        pesanan_doc = {
            'tanggal_pemesanan': tanggal_pemesanan, 
            'layanan_id': ObjectId(layanan_id),
            'paket_id': ObjectId(paket_id),
            'nama_klien': nama_klien,
            'nama_orang_tua': nama_orang_tua,
            'telepon_orang_tua': telepon_orang_tua,
            'email_klien': email_klien,
            'telepon_klien': telepon_klien,
            'whatsapp_klien': whatsapp_klien,
            'instagram_klien': instagram_klien,
            'facebook_klien': facebook_klien,
            'jam_acara': jam_acara,
            'tanggal_mulai_acara': tanggal_mulai_acara, # Store as datetime object
            'tanggal_selesai_acara': tanggal_selesai_acara, # Store as datetime object
            'lokasi_luar_labuhanbatu': lokasi_luar,
            'lokasi_id': lokasi_id_db, # Will be ObjectId if chosen from list, None if custom
            'alamat_lokasi_acara': alamat_lokasi_final,
            'link_maps_acara': link_maps_final,
            'surat_izin_lokasi': surat_izin_lokasi_filename,
            'biaya_transportasi_akomodasi': biaya_transportasi, # Currently 0, admin updates this
            'biaya_tambahan_hari': biaya_tambahan_hari,
            'biaya_lokasi': biaya_lokasi,
            'harga_paket': harga_paket, # Store base package price from form
            'deposit': deposit_paket,    # Store base deposit from form
            'total_harga': recalculated_total_harga, # Store calculated total
            'sisa_bayar': recalculated_sisa_bayar,    # Store calculated remaining payment
            'status_pesanan': 'Menunggu Konfirmasi',
            'created_at': datetime.utcnow()
        }

        db.pesanan.insert_one(pesanan_doc)
        flash("Pesanan berhasil dibuat!", "success")
        return redirect(url_for("ripe_menunggu_konfirmasi")) 

    except Exception as e:
        print(f"Error adding order: {e}")
        flash(f"Terjadi kesalahan saat menambahkan pesanan: {e}", "danger")
        
        return redirect(url_for('booking', paket_id=request.form.get('paket_id')))
 
# User - Menunggu Konfirmasi (GET request)
@app.route('/ripe_menunggu_konfirmasi')
@login_required
def ripe_menunggu_konfirmasi():
    all_pesanan_list = []
    try:
        # Ambil semua pesanan dari database
        pesanan_cursor = db.pesanan.find().sort('created_at', -1) # Urutkan dari yang terbaru

        # Buat map nama layanan, paket, dan lokasi berdasarkan _id
        layanan_map = {str(l['_id']): l['nama'] for l in db.layanan.find()}
        paket_map = {str(l['_id']): l['nama'] for l in db.paket.find()}
        lokasi_map = {str(l['_id']): l['nama'] for l in db.lokasi.find()}

        for pesanan in pesanan_cursor:
            # Konversi ObjectId pesanan ke string
            pesanan['_id'] = str(pesanan['_id'])

            # Layanan
            layanan_id = str(pesanan.get('layanan_id', ''))
            pesanan['layanan'] = layanan_map.get(layanan_id, 'Tidak ditemukan')

            # Paket
            paket_id = str(pesanan.get('paket_id', ''))
            pesanan['paket'] = paket_map.get(paket_id, 'Tidak ditemukan')

            # Lokasi (bisa None atau kosong jika input manual)
            lokasi_id = str(pesanan.get('lokasi_id', ''))
            if lokasi_id and lokasi_id != "None":
                pesanan['lokasi'] = lokasi_map.get(lokasi_id, 'Tidak ditemukan')
            else:
                pesanan['lokasi'] = 'Lokasi pilihan sendiri' if pesanan.get('alamat_lokasi_acara') else 'Tidak tersedia'

            # Format tanggal
            if isinstance(pesanan.get('tanggal_mulai_acara'), datetime):
                pesanan['tanggal_mulai_acara_formatted'] = tanggal_id(pesanan['tanggal_mulai_acara'])
            else:
                pesanan['tanggal_mulai_acara_formatted'] = 'N/A' # Fallback for missing or invalid date
            if isinstance(pesanan.get('tanggal_selesai_acara'), datetime):
                pesanan['tanggal_selesai_acara_formatted'] = tanggal_id(pesanan['tanggal_selesai_acara'])
            else:
                pesanan['tanggal_selesai_acara_formatted'] = 'N/A' # Fallback for missing or invalid date

            all_pesanan_list.append(pesanan)

        return render_template('user/ripe_menunggu_konfirmasi.html', pesanan=all_pesanan_list, current_route=request.path)

    except Exception as e:
        flash(f"Terjadi kesalahan saat mengambil data jadwal: {e}", "danger")
        # Jika terjadi kesalahan, Anda bisa me-render template dengan daftar kosong
        # atau redirect ke halaman dashboard admin.
        return render_template('user/ripe_menunggu_konfirmasi.html', pesanan=[], current_route=request.path)


# Admin - Tim Fotografi
@app.route('/admin_timFotografi')
def admin_timFotografi():
    tim = list(db.tim.find())
    return render_template('admin/timFotografi.html',
tim=tim, current_route=request.path)

@app.route('/admin_timFotografi_tambah', methods=['GET', 'POST'])
def admin_timFotografi_tambah():
    tim_exists = False

    if request.method == 'POST':
        nama = request.form['nama']
        email = request.form['email']
        telepon = request.form['telepon']
        peran = request.form.getlist('peran[]')
        gambar = request.files.get('gambar')

        # Cek apakah nama tim sudah ada
        existing_tim = db.tim.find_one({'nama': nama})
        if existing_tim:
            tim_exists = True
        else:
            if gambar:
                nama_file_asli = gambar.filename
                nama_file_gambar = nama_file_asli.split('/')[-1]
                file_path = f'static/images/imgTim/{nama_file_gambar}'
                gambar.save(file_path)
            else:
                nama_file_gambar = None

            doc = {
                'nama': nama,
                'email': email,
                'telepon': telepon,
                'peran': peran,
                'gambar': nama_file_gambar
            }
            db.tim.insert_one(doc)
            return redirect(url_for("admin_timFotografi"))

    return render_template('admin/timFotografi_tambah.html', tim_exists=tim_exists)


@app.route('/check_nama_tim', methods=['POST'])
def check_nama_tim():
    data = request.json
    nama_tim = data.get('nama', '')

    # Periksa apakah nama tim sudah ada di database MongoDB
    existing_tim = db.tim.find_one({'nama': {'$regex': f'^{nama_tim}$', '$options': 'i'}}) 
    if existing_tim:
        return jsonify({'exists': True})
    else:
        return jsonify({'exists': False})

@app.route('/admin_timFotografi_ubah/<tim_id>', methods=['GET', 'POST'])
def admin_timFotografi_ubah(tim_id):
    tim = db.tim.find_one({'_id': ObjectId(tim_id)})
    if not tim:
        # Handle case where tim is not found
        return redirect(url_for('admin_timFotografi'))

    if request.method == 'POST':
        nama = request.form['nama']
        email = request.form['email']
        telepon = request.form['telepon']
        peran = request.form.getlist('peran[]')
        gambar_baru = request.files.get('gambar')

        # Cek apakah nama tim sudah ada untuk tim lain
        existing_tim_with_name = db.tim.find_one({
            'nama': {'$regex': f'^{nama}$', '$options': 'i'},
            '_id': {'$ne': ObjectId(tim_id)}  # Pastikan bukan tim yang sedang diubah
        })

        if existing_tim_with_name:
            # Jika nama sudah ada pada tim lain, tampilkan pesan error
            return render_template('admin/timFotografi_ubah.html', tim=tim, tim_exists=True)
        
        # Perbarui gambar jika ada yang baru diupload
        nama_file_gambar = tim.get('gambar') # Ambil nama gambar lama
        if gambar_baru and allowed_file(gambar_baru.filename):
            # Hapus gambar lama jika ada dan berbeda dengan yang baru
            if nama_file_gambar and nama_file_gambar != secure_filename(gambar_baru.filename):
                old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], nama_file_gambar)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            
            filename = secure_filename(gambar_baru.filename)
            gambar_baru.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            nama_file_gambar = filename # Perbarui dengan nama gambar baru

        db.tim.update_one(
            {'_id': ObjectId(tim_id)},
            {'$set': {
                'nama': nama,
                'email': email,
                'telepon': telepon,
                'peran': peran,
                'gambar': nama_file_gambar
            }}
        )
        return redirect(url_for('admin_timFotografi'))
    
    return render_template('admin/timFotografi_ubah.html', tim=tim, tim_exists=False)


@app.route('/toggle_tim_status/<tim_id>', methods=['POST'])
def toggle_tim_status(tim_id):
    try:
        tim = db.tim.find_one({'_id': ObjectId(tim_id)})
        if tim:
            current_status = tim.get('aktif', False) # Default ke False jika tidak ada
            new_status = not current_status
            db.tim.update_one(
                {'_id': ObjectId(tim_id)},
                {'$set': {'aktif': new_status}}
            )
            return jsonify({'success': True, 'new_status': new_status})
        return jsonify({'success': False, 'message': 'Tim tidak ditemukan'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# User - Tentang Kami
@app.route('/tentang-kami')
def tentang_kami():
    # Hanya mengambil tim yang statusnya 'aktif': True
    tim_aktif = list(db.tim.find({'aktif': True}))
    return render_template('user/tentang_kami.html', tim=tim_aktif, current_route=request.path)





# FAQ

# Koleksi FAQ
koleksi_faqs = db.faqs

@app.route('/admin_faq')
def admin_faq():
    """Menampilkan daftar semua FAQ (pending dan published) untuk admin."""
    # Urutkan berdasarkan tanggal diperbarui (terbaru di atas) dan status (pending di atas)
    daftar_faqs = list(koleksi_faqs.find().sort([("status", 1), ("tanggal_diajukan", -1)]))
    return render_template('admin/faq.html', faqs=daftar_faqs)

@app.route('/admin_faq_tambah', methods=['GET', 'POST'])
def admin_faq_tambah():
    """Menampilkan dan memproses formulir tambah FAQ manual oleh admin."""
    if request.method == 'POST':
        pertanyaan = request.form['pertanyaan'].strip()
        jawaban = request.form['jawaban'].strip()

        if not pertanyaan or not jawaban:
            # Tidak menggunakan flash, langsung render template dengan pesan error
            return render_template('admin/faq_tambah.html', error_message='Pertanyaan dan jawaban tidak boleh kosong.', data_input=request.form)

        # Cek apakah pertanyaan sudah ada untuk menghindari duplikasi
        faq_sudah_ada = koleksi_faqs.find_one({"pertanyaan": {"$regex": pertanyaan, "$options": "i"}})
        if faq_sudah_ada:
            # Tidak menggunakan flash, langsung render template dengan pesan error
            return render_template('admin/faq_tambah.html', error_message='Pertanyaan ini sudah ada.', data_input=request.form)

        dokumen_faq_baru = {
            "nama_pengaju": "Admin", # Atau biarkan kosong jika tidak relevan untuk FAQ manual
            "email_pengaju": "",     # Atau biarkan kosong
            "pertanyaan": pertanyaan,
            "jawaban": jawaban,
            "status": "published",   # Langsung published jika ditambahkan admin
            "is_active": True,       # Default aktif jika ditambahkan admin
            "tanggal_diajukan": datetime.now(),
            "tanggal_diperbarui": datetime.now()
        }
        koleksi_faqs.insert_one(dokumen_faq_baru)
        # Tidak menggunakan flash, SweetAlert di frontend akan menangani sukses
        return redirect(url_for('admin_faq'))

    return render_template('admin/faq_tambah.html')

@app.route('/admin_faq_ubah/<id_faq>', methods=['GET', 'POST'])
def admin_faq_ubah(id_faq):
    """Menampilkan dan memproses formulir ubah FAQ oleh admin."""
    try:
        faq_untuk_diubah = koleksi_faqs.find_one({"_id": ObjectId(id_faq)})
        if not faq_untuk_diubah:
            flash('FAQ tidak ditemukan.', 'danger') # Flash masih bisa digunakan untuk error penting
            return redirect(url_for('admin_faq'))
    except Exception as e:
        flash(f'ID FAQ tidak valid: {e}', 'danger')
        return redirect(url_for('admin_faq'))

    if request.method == 'POST':
        jawaban_baru = request.form['jawaban'].strip()
        pertanyaan_baru = request.form['pertanyaan'].strip() # Admin bisa mengedit pertanyaan juga

        if not pertanyaan_baru or not jawaban_baru:
            return render_template('admin/faq_ubah.html', faq=faq_untuk_diubah, error_message='Pertanyaan dan jawaban tidak boleh kosong.')

        # Update FAQ di database
        koleksi_faqs.update_one(
            {"_id": ObjectId(id_faq)},
            {
                "$set": {
                    "pertanyaan": pertanyaan_baru,
                    "jawaban": jawaban_baru,
                    "status": "published", # Otomatis published setelah diubah
                    "tanggal_diperbarui": datetime.now()
                }
            }
        )
        # Tidak menggunakan flash untuk sukses, SweetAlert di frontend akan menangani
        return redirect(url_for('admin_faq'))

    return render_template('admin/faq_ubah.html', faq=faq_untuk_diubah)

@app.route('/admin_faq_toggle_status/<id_faq>', methods=['POST'])
def admin_faq_toggle_status(id_faq):
    """Mengubah status aktif/nonaktif FAQ."""
    try:
        faq = koleksi_faqs.find_one({"_id": ObjectId(id_faq)})
        if not faq:
            return jsonify({"success": False, "message": "FAQ tidak ditemukan."}), 404

        new_status = not faq.get("is_active", False) # Default ke False jika tidak ada
        koleksi_faqs.update_one(
            {"_id": ObjectId(id_faq)},
            {"$set": {"is_active": new_status, "tanggal_diperbarui": datetime.now()}}
        )
        return jsonify({"success": True, "new_is_active": new_status, "message": "Status berhasil diperbarui."})
    except Exception as e:
        logging.error(f"Error toggling FAQ status for ID {id_faq}: {e}")
        return jsonify({"success": False, "message": f"Terjadi kesalahan: {e}"}), 500




@app.route('/faqbb')
def faq_user():
    """Menampilkan daftar FAQ yang berstatus 'published' dan 'aktif' untuk user."""
    daftar_faqs = list(koleksi_faqs.find({"status": "published", "is_active": True}).sort("tanggal_diperbarui", -1))
    return render_template('user/faq.html', faqs=daftar_faqs)

@app.route('/formfaq', methods=['GET', 'POST'])
def form_faq_user():
    """Menampilkan dan memproses formulir pertanyaan dari user."""
    if request.method == 'POST':
        print("Menerima request POST untuk formfaq.")

        # Gunakan .get() untuk menghindari KeyError jika field tidak ditemukan
        nama_pengaju = request.form.get('nama_klien')
        email_pengaju = request.form.get('email')
        pertanyaan = request.form.get('pertanyaan_user') # <--- KONSISTENSI NAMA FIELD DENGAN HTML

        print(f"Data form diterima: Nama='{nama_pengaju}', Email='{email_pengaju}', Pertanyaan='{pertanyaan}'")

        if not nama_pengaju or not email_pengaju or not pertanyaan:
            print("Validasi Gagal: Ada kolom yang kosong.")
            # Flash message jika ada error, atau teruskan error_message ke template
            flash('Harap lengkapi semua kolom yang wajib diisi.', 'danger')
            return render_template('user/faq_form.html', data_input=request.form)

        # Cek format email dasar
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email_pengaju):
            print("Validasi Gagal: Format email tidak valid.")
            flash('Format email tidak valid.', 'danger')
            return render_template('user/faq_form.html', data_input=request.form)

        try:
            dokumen_faq_baru = {
                "nama_pengaju": nama_pengaju,
                "email_pengaju": email_pengaju,
                "pertanyaan": pertanyaan,
                "jawaban": "", # Kosongkan karena masih pending
                "status": "pending",
                "is_active": False, # Default nonaktif saat pertama kali diajukan oleh user
                "tanggal_diajukan": datetime.now(),
                "tanggal_diperbarui": datetime.now()
            }
            koleksi_faqs.insert_one(dokumen_faq_baru)
            print("FAQ user berhasil disimpan dengan ID:", dokumen_faq_baru.get('_id'))
            # Kita tidak menggunakan flash message sukses di sini karena SweetAlert akan menangani
            return redirect(url_for('faq_user')) # Redirect ke halaman FAQ utama user setelah berhasil
        except Exception as e:
            print(f"Error saat menyimpan FAQ ke database: {e}")
            flash('Terjadi kesalahan saat mengirim pertanyaan. Silakan coba lagi.', 'danger')
            return render_template('user/faq_form.html', data_input=request.form)

    print("Menerima request GET untuk formfaq.")
    return render_template('user/faq_form.html')



@app.route('/admin_login')
def admin_login():
    return render_template('admin/login_admin.html')

@app.route('/admin_logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))







@app.route('/jadwal')
def jadwal():
    return render_template('user/jadwal.html')




@app.route('/pembayaran')
def pembayaran():
    return render_template('user/pembayaran.html')

@app.route('/ulasan')
def ulasan():
    return render_template('user/ulasan.html')

@app.route('/riwayat_pemesanan')
def riwayat_pemesanan():
    return render_template('user/riwayat_pemesanan.html')






@app.route('/kontak')
def kontak():
    return render_template('user/kontak.html')

@app.route('/faqbb')
def faq():
    return render_template('user/faq.html')







#Login User
@app.route('/masuk')
def masuk():
    return render_template('user/login_user.html')

@app.route('/daftar')
def daftar():
    return render_template('user/daftar.html')

@app.route('/lupa_kataSandi')
def lupa_kataSandi():
    return render_template('user/lupa_kataSandi.html')


@app.route('/reset_password/<token>')
def reset_password(token):
    try:
        payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
        email = payload.get('email')
        exp = payload.get('exp')

        if datetime.now().timestamp() > exp:
            return render_template('user/reset_password.html', message="Tautan reset password sudah kadaluarsa. Silakan coba lagi.", error=True)

        user = users_collection.find_one({"email": email})
        if not user:
            return render_template('user/reset_password.html', message="Pengguna tidak ditemukan.", error=True)

        return render_template('user/reset_password.html', token=token, email=email)
    except jwt.ExpiredSignatureError:
        return render_template('user/reset_password.html', message="Tautan reset password sudah kadaluarsa. Silakan coba lagi.", error=True)
    except jwt.InvalidTokenError:
        return render_template('user/reset_password.html', message="Tautan reset password tidak valid.", error=True)
    except Exception as e:
        print(f"Error accessing reset password page: {e}")
        return render_template('user/reset_password.html', message="Terjadi kesalahan. Silakan coba lagi.", error=True)


# --- API Routes (Sama seperti sebelumnya untuk daftar dan masuk) ---

@app.route('/api/daftar', methods=['POST'])
def api_daftar():
    data = request.get_json()
    full_name = data.get('namalengkap')
    username = data.get('username')
    email = data.get('alamatemail')
    password = data.get('password')
    konfirpassword = data.get('konfirpassword')

    if not all([full_name, username, email, password, konfirpassword]):
        return jsonify({"success": False, "message": "Semua field harus diisi."}), 400

    if not is_valid_email(email):
        return jsonify({"success": False, "message": "Format email tidak valid."}), 400

    if password != konfirpassword:
        return jsonify({"success": False, "message": "Konfirmasi kata sandi tidak cocok."}), 400

    if len(password) < 6:
        return jsonify({"success": False, "message": "Kata sandi harus minimal 6 karakter."}), 400

    if users_collection.find_one({"username": username}):
        return jsonify({"success": False, "message": "Nama pengguna sudah terdaftar."}), 409
    if users_collection.find_one({"email": email}):
        return jsonify({"success": False, "message": "Email sudah terdaftar."}), 409

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    try:
        users_collection.insert_one({
            "full_name": full_name,
            "username": username,
            "email": email,
            "password_hash": hashed_password,
            "created_at": datetime.now(),
            "profile_picture_url": "https://storage.googleapis.com/a1aa/image/10b4ac45-2b8b-450f-888c-bd7182757e8a.jpg" # Inisialisasi dengan string kosong atau URL default
        })
        return jsonify({"success": True, "message": "Pendaftaran berhasil! Silakan masuk."}), 201
    except Exception as e:
        print(f"Error during registration: {e}")
        return jsonify({"success": False, "message": "Terjadi kesalahan saat pendaftaran. Silakan coba lagi."}), 500

@app.route('/api/masuk', methods=['POST'])
def api_masuk():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"success": False, "message": "Nama pengguna dan kata sandi harus diisi."}), 400

    user = users_collection.find_one({"username": username})

    if user and check_password_hash(user['password_hash'], password):
        session['user_id'] = str(user['_id'])
        session['username'] = user['username']
        session['full_name'] = user.get('full_name', '')
        session['email'] = user.get('email', '')
        # Menggunakan path UPLOAD_FOLDER + filename, jika kosong pakai default
        session['profile_picture_url'] = user.get('profile_picture_url', '') or "https://storage.googleapis.com/a1aa/image/10b4ac45-2b8b-450f-888c-bd7182757e8a.jpg"
        return jsonify({"success": True, "message": "Login berhasil!"}), 200
    else:
        return jsonify({"success": False, "message": "Nama pengguna atau kata sandi salah."}), 401

@app.route('/api/lupa_kataSandi', methods=['POST'])
def api_lupa_kataSandi():
    data = request.get_json()
    email_dest = data.get('email')

    if not email_dest:
        return jsonify({"success": False, "message": "Email harus diisi."}), 400

    user = users_collection.find_one({"email": email_dest})

    if not user:
        return jsonify({"success": False, "message": "Email tidak terdaftar."}), 404

    user_display_name = user.get('full_name', user.get('username', 'Pengguna'))

    payload = {
        "email": email_dest,
        "exp": datetime.utcnow() + timedelta(minutes=app.config['PASSWORD_RESET_TIMEOUT_MINUTES'])
    }
    token = jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm="HS256")

    reset_link = url_for('reset_password', token=token, _external=True)

    try:
        msg = Message("Ubah Kata Sandi Akun Oval Photo Anda",
                      sender=app.config['MAIL_DEFAULT_SENDER'],
                      recipients=[email_dest])

        msg.html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: sans-serif;
                    line-height: 1.6;
                    color: #black;
                }}
                p {{ margin-bottom: 1em; }}
                strong {{ font-weight: bold; }}
                a {{
                    color: #F7BF52;
                    text-decoration: none;
                    font-weight: bold;
                }}
                a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <p style="font-weight: bold; font-size: 1.2em;">Halo, {user_display_name}!</p>
            <p>Kami baru saja menerima permintaan untuk mengubah kata sandi akun kamu. Jika kamu mengajukan permintaan ini, kamu dapat mengklik tautan di bawah ini untuk mengubah kata sandi kamu.</p>
            <p><a href="{reset_link}">Klik di sini untuk mengubah kata sandi kamu</a></p>
            <p>Tautan ini akan kadaluarsa dalam {app.config['PASSWORD_RESET_TIMEOUT_MINUTES']} menit, jadi pastikan untuk menggunakannya sebelum waktu habis. Jika kamu tidak mengajukan permintaan untuk mengubah kata sandi, kamu bisa mengabaikan email ini.</p>
            <p>Terima kasih,</p>
            <p style="font-weight: bold;">Oval Photo</p>
        </body>
        </html>
        """

        mail.send(msg)
        print(f"--- Email reset password berhasil dikirim ke {email_dest} ({user_display_name}) ---")
        return jsonify({"success": True, "message": "Oval Photo telah mengirimkan tautan untuk mengubah atau mereset password yang dikirimkan melalui email."}), 200
    except Exception as e:
        print(f"Error sending email: {e}")
        return jsonify({"success": False, "message": "Terjadi kesalahan saat mengirim email reset password. Silakan coba lagi nanti."}), 500

@app.route('/api/reset_password', methods=['POST'])
def api_reset_password():
    data = request.get_json()
    token = data.get('token')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')

    if not all([token, new_password, confirm_password]):
        return jsonify({"success": False, "message": "Semua field harus diisi."}), 400

    if new_password != confirm_password:
        return jsonify({"success": False, "message": "Kata sandi baru dan konfirmasi tidak cocok."}), 400

    if len(new_password) < 6:
        return jsonify({"success": False, "message": "Kata sandi harus minimal 6 karakter."}), 400

    try:
        payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
        email = payload.get('email')

        user = users_collection.find_one({"email": email})
        if not user:
            return jsonify({"success": False, "message": "Pengguna tidak ditemukan."}), 404

        hashed_new_password = generate_password_hash(new_password, method='pbkdf2:sha256')
        users_collection.update_one(
            {"email": email},
            {"$set": {"password_hash": hashed_new_password}}
        )
        return jsonify({"success": True, "message": "Kata sandi Anda berhasil diubah. Silakan masuk dengan kata sandi baru Anda."}), 200

    except jwt.ExpiredSignatureError:
        return jsonify({"success": False, "message": "Tautan reset password sudah kadaluarsa. Silakan coba lagi."}), 401
    except jwt.InvalidTokenError:
        return jsonify({"success": False, "message": "Tautan reset password tidak valid."}), 401
    except Exception as e:
        print(f"Error during password reset: {e}")
        return jsonify({"success": False, "message": "Terjadi kesalahan saat mengubah kata sandi. Silakan coba lagi."}), 500


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('full_name', None)
    session.pop('email', None)
    session.pop('profile_picture_url', None)
    flash("Anda telah logout.", "info")
    return redirect(url_for('masuk'))






# PROFIL USER 
# --- API Get Profile ---
@app.route('/api/profil/update', methods=['POST'])
@login_required
def api_update_profil():
    user_id = session['user_id']
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        print(f"DEBUG: User with ID {user_id} not found in DB.") # Tambahkan ini
        return jsonify({"success": False, "message": "Pengguna tidak ditemukan."}), 404

    data = request.form
    full_name = data.get('name')
    username = data.get('username')
    email = data.get('email')
    photo = request.files.get('photo')

    print(f"DEBUG: Received update request for user {user_id}") # Tambahkan ini
    print(f"DEBUG: Name: {full_name}, Username: {username}, Email: {email}") # Tambahkan ini

    if photo:
        print(f"DEBUG: Photo file received: {photo.filename}") # Tambahkan ini
        if photo.filename == '':
            print("DEBUG: No filename provided for photo.") # Tambahkan ini
            return jsonify({"success": False, "message": "Tidak ada file yang dipilih untuk diunggah."}), 400
        if not allowed_file(photo.filename):
            print(f"DEBUG: File extension not allowed: {photo.filename}") # Tambahkan ini
            return jsonify({"success": False, "message": "Format file tidak didukung. Gunakan PNG, JPG, JPEG, atau GIF."}), 400

        filename = secure_filename(f"{user_id}_{int(time.time())}_{photo.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # DEBUG: Cek apakah folder upload benar-benar ada dan bisa ditulis
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            print(f"DEBUG ERROR: UPLOAD_FOLDER does not exist: {app.config['UPLOAD_FOLDER']}")
            return jsonify({"success": False, "message": "Folder penyimpanan tidak ditemukan di server."}), 500
        if not os.access(app.config['UPLOAD_FOLDER'], os.W_OK):
            print(f"DEBUG ERROR: UPLOAD_FOLDER is not writable: {app.config['UPLOAD_FOLDER']}")
            return jsonify({"success": False, "message": "Folder penyimpanan tidak dapat ditulis."}), 500


        try:
            photo.save(filepath)
            print(f"DEBUG: Photo saved to: {filepath}") # Tambahkan ini
            updates = {} # Pastikan updates diinisialisasi
            updates['profile_picture_url'] = f"/gambar_profil_user/{filename}"
            print(f"DEBUG: Setting profile_picture_url to: {updates['profile_picture_url']}") # Tambahkan ini
        except Exception as e:
            print(f"DEBUG ERROR: Error saving image: {e}") # Tambahkan ini
            return jsonify({"success": False, "message": "Gagal menyimpan foto profil."}), 500
    else:
        print("DEBUG: No photo file provided.") # Tambahkan ini
        updates = {} # Pastikan updates diinisialisasi untuk kasus tanpa foto

    # ... (bagian validasi nama, username, email seperti sebelumnya) ...
    if full_name and full_name != user.get('full_name'):
        updates['full_name'] = full_name
    if email and email != user.get('email'):
        if not is_valid_email(email):
            return jsonify({"success": False, "message": "Format email tidak valid."}), 400
        if users_collection.find_one({"email": email, "_id": {"$ne": ObjectId(user_id)}}):
            return jsonify({"success": False, "message": "Email sudah terdaftar oleh pengguna lain."}), 409
        updates['email'] = email
    if username and username != user.get('username'):
        if users_collection.find_one({"username": username, "_id": {"$ne": ObjectId(user_id)}}):
            return jsonify({"success": False, "message": "Username sudah digunakan oleh pengguna lain."}), 409
        updates['username'] = username


    if updates:
        print(f"DEBUG: Updating DB with: {updates}") # Tambahkan ini
        try:
            users_collection.update_one({"_id": ObjectId(user_id)}, {"$set": updates})
            updated_user = users_collection.find_one({"_id": ObjectId(user_id)})
            session['full_name'] = updated_user.get('full_name', '')
            session['username'] = updated_user.get('username', '')
            session['email'] = updated_user.get('email', '')
            session['profile_picture_url'] = updated_user.get('profile_picture_url', '') or '/static/default_profile_pic.png'
            print(f"DEBUG: Session profile_picture_url after update: {session['profile_picture_url']}") # Tambahkan ini
            return jsonify({"success": True, "message": "Profil berhasil diperbarui."}), 200
        except Exception as e:
            print(f"DEBUG ERROR: Error updating profile in database: {e}") # Tambahkan ini
            return jsonify({"success": False, "message": "Gagal memperbarui profil."}), 500
    else:
         print("DEBUG: No updates to perform (no changes detected).") # Tambahkan ini
         return jsonify({"success": True, "message": "Tidak ada perubahan yang dilakukan."}), 200

# ... (pastikan juga di bagian api_get_profil) ...
@app.route('/api/profil', methods=['GET'])
@login_required
def api_get_profil():
    user_id = session['user_id']
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if user:
        profile_pic_url = user.get('profile_picture_url', '') or "https://storage.googleapis.com/a1aa/image/10b4ac45-2b8b-450f-888c-bd7182757e8a.jpg"
        print(f"DEBUG: Sending profile data for {user_id}, photo_url: {profile_pic_url}")
        return jsonify({
            "success": True,
            "full_name": user.get('full_name', ''),
            "username": user.get('username', ''),
            "email": user.get('email', ''),
            "profile_picture_url": profile_pic_url
        }), 200
    else:
        print(f"DEBUG: User {user_id} not found when fetching profile.")
        return jsonify({"success": False, "message": "Pengguna tidak ditemukan."}), 404


# --- API untuk Menghapus Foto Profil ---
@app.route('/api/profil/delete_photo', methods=['POST'])
@login_required
def api_delete_profile_photo():
    user_id = session['user_id']
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    
    if not user:
        return jsonify({"success": False, "message": "Pengguna tidak ditemukan."}), 404

    current_photo_url = user.get('profile_picture_url')

    # Periksa apakah foto saat ini adalah foto default GCS atau kosong
    if not current_photo_url or current_photo_url == DEFAULT_GCS_PROFILE_PIC_URL:
        return jsonify({"success": False, "message": "Tidak ada foto profil yang dapat dihapus."}), 400

    # Ekstrak nama file dari URL
    # URL contoh: /gambar_profil_user/some_filename.png
    # Kita hanya perlu 'some_filename.png'
    filename_from_url = os.path.basename(current_photo_url)
    filepath_to_delete = os.path.join(app.config['UPLOAD_FOLDER'], filename_from_url)
    
    print(f"DEBUG: Mencoba menghapus file: {filepath_to_delete}")

    # Hapus file fisik dari server
    try:
        if os.path.exists(filepath_to_delete):
            os.remove(filepath_to_delete)
            print(f"DEBUG: File {filepath_to_delete} berhasil dihapus.")
        else:
            print(f"DEBUG: File {filepath_to_delete} tidak ditemukan, mungkin sudah dihapus atau URL salah.")
            # Kita tetap lanjutkan update DB meskipun file tidak ditemukan, anggap saja sudah tidak ada
    except Exception as e:
        print(f"DEBUG ERROR: Gagal menghapus file {filepath_to_delete}: {e}")
        return jsonify({"success": False, "message": f"Terjadi kesalahan saat menghapus file: {e}"}), 500

    # Perbarui database dan sesi
    try:
        users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"profile_picture_url": DEFAULT_GCS_PROFILE_PIC_URL}} # Set kembali ke default GCS
        )
        session['profile_picture_url'] = DEFAULT_GCS_PROFILE_PIC_URL
        print(f"DEBUG: URL foto profil di DB dan sesi diubah ke default GCS.")
        return jsonify({"success": True, "message": "Foto profil berhasil dihapus."}), 200
    except Exception as e:
        print(f"DEBUG ERROR: Gagal memperbarui DB setelah menghapus foto: {e}")
        return jsonify({"success": False, "message": "Gagal memperbarui database setelah penghapusan foto."}), 500

# ... (akhir kode) ...

# --- Route untuk menyajikan file dari folder upload ---
# --- PERUBAHAN DI SINI ---
@app.route('/gambar_profil_user/<filename>')
def uploaded_file(filename):
    safe_filename = secure_filename(filename)
    # Ini akan melayani file langsung dari direktori 'upload/profile_pictures'
    return send_from_directory(app.config['UPLOAD_FOLDER'], safe_filename)
# --- AKHIR PERUBAHAN ---


# --- Profil User (Tampilan HTML, Dilindungi Login) ---
@app.route('/profil')
@login_required
def profil_user():
    return render_template('user/profil_user.html')

@app.route('/profiledit')
@login_required
def profiledit():
    return render_template('user/profil_edit.html')






# Akun Klien
@app.route('/admin_akunKlien')
# Tambahkan decorator @admin_login_required di sini jika admin memiliki sistem login terpisah
def admin_akunKlien():
    # Mengambil semua user dari koleksi 'users' di MongoDB
    users_data = list(db.users.find())

    print(f"DEBUG: Jumlah user yang ditemukan di database: {len(users_data)}") # --- TAMBAHKAN INI ---
    if users_data:
        print(f"DEBUG: Contoh data user pertama: {users_data[0]}") # --- TAMBAHKAN INI ---
    else:
        print("DEBUG: Tidak ada user ditemukan di database.") # --- TAMBAHKAN INI ---

    # Untuk setiap user, pastikan profile_picture_url diisi dengan default jika kosong di database
    for user in users_data:
        if not user.get('profile_picture_url'):
            user['profile_picture_url'] = DEFAULT_GCS_PROFILE_PIC_URL
        user['_id'] = str(user['_id']) # Pastikan _id diubah ke string

    # Mengirim data user ke template 'admin/akunKlien.html'
    return render_template('admin/akunKlien.html', users=users_data, current_route=request.path)


























@app.route('/ripe_diproses')
@login_required
def ripe_diproses():
    return render_template('user/ripe_diproses.html')

@app.route('/ripe_selesai')
@login_required
def ripe_selesai():
    return render_template('user/ripe_selesai.html')





@app.route('/formulasan')
def formulasan():
    return render_template('user/ulasan_form.html')






















if __name__ == '__main__':
    # Memastikan folder upload ada saat aplikasi dimulai
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    if app.config['SECRET_KEY'] == 'DANANDA34' or \
       app.config['JWT_SECRET_KEY'] == 'KILLING23':
        print("WARNING: Using default secret keys. Please set FLASK_SECRET_KEY and JWT_SECRET_KEY environment variables in production for security.")
    app.run('0.0.0.0', port=5000, debug=True)
