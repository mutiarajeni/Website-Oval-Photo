from flask import Flask, request, render_template, redirect, url_for, session, flash, jsonify
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

# Koneksi ke database MongoDB
connection_string = "mongodb+srv://test:sparta@cluster0.9kunvma.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(connection_string)
db = client.dbfotografi

app = Flask(__name__)
app.secret_key = 'super-secret-key' 

# Route untuk halaman user
@app.route('/')
def beranda():
    return render_template('user/beranda.html')







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




# User - Katalog Layanan
@app.route("/katalog_layanan")
def katalog_layanan():
    layanan = list(db.layanan.find({ "status": True }))   # hanya yang aktif
    return render_template(
        "user/katalog_layanan.html",
        layanan=layanan,
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
    paket = list(db.paket.find().sort('created_at', -1))
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
    galeri=list(db.galeri.find())
    return render_template('admin/galeri.html', galeri=galeri, current_route=request.path)

@app.route('/admin_galeri_tambah', methods=['GET', 'POST'])
def admin_galeri_tambah():
    layanan = list(db.layanan.find())
    lokasi = list(db.lokasi.find())

    if request.method == 'POST':
        kategori = request.form.get('kategori')
        layanan_id = request.form.get('layanan')
        lokasi_id = request.form.get('lokasi')
        gambar_files = request.files.getlist('gambar[]')

        if not kategori or not gambar_files:
            flash("Kategori dan gambar wajib diisi.", "danger")
            return redirect(url_for('admin_galeri_tambah'))

        nama_file_gambar = []
        for gambar in gambar_files:
            if gambar and gambar.filename:
                nama_file = secure_filename(gambar.filename)
                simpan_path = os.path.join('static/images/imgGaleri', nama_file)
                gambar.save(simpan_path)
                nama_file_gambar.append(nama_file)

        doc = {
            'kategori': kategori,
            'gambar': nama_file_gambar,
            'id_layanan': ObjectId(layanan_id) if layanan_id else None,
            'id_lokasi': ObjectId(lokasi_id) if lokasi_id else None,
            'tanggal_upload': datetime.now()
        }

        db.galeri.insert_one(doc)
        return redirect(url_for('admin_galeri'))

    return render_template('admin/galeri_tambah.html',
                           layanan=layanan,
                           lokasi=lokasi,
                           current_route=request.path)

@app.route('/admin_galeri_ubah')
def admin_galeri_ubah():
    return render_template('admin/galeri_ubah.html')

@app.route('/galeri')
def galeri():
    return render_template('user/galeri.html')






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
                'biaya': biaya
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

@app.route('/admin_lokasi_ubah')
def admin_lokasi_ubah():
    return render_template('admin/lokasi_ubah.html')







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
                pesanan['lokasi'] = '(Lokasi Manual)' if pesanan.get('alamat_lokasi_acara') else 'Tidak tersedia'

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



@app.route('/admin_jadwal_ubah')
def admin_jadwal_ubah():
    return render_template('admin/jadwal_ubah.html')








# Pesanan
# --- Routes API untuk Frontend ---

@app.route('/api/all_paket', methods=['GET'])
def api_all_paket():
    """Mengembalikan semua data paket, termasuk harga dan deposit."""
    paket_data = list(db.paket.find())
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
    lokasi_data = list(db.lokasi.find())
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
            layanan_list = list(db.layanan.find())
            lokasi_list = list(db.lokasi.find())
            for layanan in layanan_list:
                layanan['_id'] = str(layanan['_id'])
            for lokasi in lokasi_list:
                lokasi['_id'] = str(lokasi['_id'])
            return render_template('user/booking.html',
                                   layanan_list=layanan_list, # Pass these back for re-rendering
                                   lokasi_list=lokasi_list,
                                   error_message=f"Terjadi kesalahan: {e}",
                                   # You might want to pass back the original form data to pre-fill
                                   # This requires more complex logic for error handling
                                   selected_paket_id=request.form.get('paket_id'),
                                   selected_layanan_id=request.form.get('layanan_id'),
                                   selected_paket_nama=request.form.get('paket_nama'), # if you passed this
                                   selected_paket_harga_raw=float(request.form.get('harga_paket_dasar', '0')),
                                   selected_paket_deposit_raw=float(request.form.get('deposit_paket_dasar', '0'))
                                   )

    # If method GET (user directly accesses /admin_pesanan_tambah, which shouldn't happen for direct user booking)
    # This part can be removed if you only expect POST requests to this route from the booking form
    layanan_list = list(db.layanan.find())
    lokasi_list = list(db.lokasi.find())
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
            pesanan['lokasi'] = '(Lokasi Manual)' if pesanan.get('alamat_lokasi_acara') else 'Tidak tersedia'

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




# Konfigurasi SMTP Gmail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'ovalphotoo@gmail.com' 
app.config['MAIL_PASSWORD'] = 'cvmo ujrb jjpp rsip'   
app.config['MAIL_DEFAULT_SENDER'] = 'ovalphotoo@gmail.com'

mail = Mail(app)

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

    lokasi_list = list(db.lokasi.find())
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
        return redirect(url_for("ripe_menunggukonfirmasi")) 

    except Exception as e:
        print(f"Error adding order: {e}")
        flash(f"Terjadi kesalahan saat menambahkan pesanan: {e}", "danger")
        # If there's an error, redirect back to the booking page with the packet ID
        # to allow the user to try again, potentially pre-filling some data if desired.
        return redirect(url_for('booking', paket_id=request.form.get('paket_id')))


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

@app.route('/admin_timFotografi_ubah')
def admin_timFotografi_ubah():
    return render_template('admin/timFotografi_ubah.html')

# User - Tentang Kami
@app.route('/tentang-kami')
def tentang_kami():
    tim = list(db.tim.find())
    return render_template('user/tentang_kami.html', tim=tim, current_route=request.path)





# FAQ
@app.route('/admin_faq')
def admin_faq():
    return render_template('admin/faq.html')

@app.route('/admin_faq_tambah')
def admin_faq_tambah():
    return render_template('admin/faq_tambah.html')

@app.route('/admin_faq_ubah')
def admin_faq_ubah():
    return render_template('admin/faq_ubah.html')

# Akun Klien
@app.route('/admin_akunKlien')
def admin_akunKlien():
    return render_template('admin/akunKlien.html')

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

@app.route('/riwayat-pemesanan')
def riwayat_pemesanan():
    return render_template('user/riwayat_pemesanan.html')



@app.route('/profil')
def profil_user():
    return render_template('user/profil_user.html')



@app.route('/kontak')
def kontak():
    return render_template('user/kontak.html')

@app.route('/faqbb')
def faq():
    return render_template('user/faq.html')

@app.route('/masuk')
def masuk():
    return render_template('user/login_user.html')

@app.route('/daftar')
def daftar():
    return render_template('user/daftar.html')

@app.route('/lupa_kataSandi')
def lupa_kataSandi():
    return render_template('user/lupa_kataSandi.html')

@app.route('/ripe_diproses')
def ripe_diproses():
    return render_template('user/ripe_diproses.html')

@app.route('/ripe_selesai')
def ripe_selesai():
    return render_template('user/ripe_selesai.html')

@app.route('/ripe_menunggukonfirmasi')
def ripe_menunggukonfirmasi():
    return render_template('user/ripe_menunggu-konfirmasi.html')

@app.route('/formfaq')
def formfaq():
    return render_template('user/faq_form.html')

@app.route('/formulasan')
def formulasan():
    return render_template('user/ulasan_form.html')

@app.route('/profiledit')
def profiledit():
    return render_template('user/profil_edit.html')




















if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
