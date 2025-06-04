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
    paket = list(db.paket.find())
    layanan_map = {str(l['_id']): l['nama'] for l in db.layanan.find()}

    # Tambahkan nama layanan ke dalam setiap dokumen paket
    for p in paket:
        layanan_id = str(p.get('layanan_id'))
        p['layanan'] = layanan_map.get(layanan_id, 'Tidak ditemukan')

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
    paket_exists=False
    
    if request.method=='POST':
        nama = request.form['nama']
        layanan_id = request.form['layanan']
        harga = int(request.form['harga'])
        deposit = int(request.form['deposit'])
        keuntungan = request.form['keuntungan']
        tim_kerja = request.form['tim_kerja']
        periode = request.form['periode']

         # Parsing tanggal dari periode input (flatpickr dengan mode range: "dd MMMM yyyy to dd MMMM yyyy")
        tanggal_mulai = tanggal_selesai = None
        if periode:
            # Ganti tanda '–' (en dash) jadi ' to ' supaya seragam
            periode = periode.replace('–', ' to ').replace('—', ' to ')
            if ' to ' in periode:
                mulai_str, selesai_str = [
                    s.strip() for s in periode.split(" to ")
                ]
            else:
                 mulai_str = selesai_str = periode.strip()

            for_parse = "%d %B %Y"           # misal: 01 Januari 2025
            try:
                tanggal_mulai   = datetime.strptime(mulai_str, for_parse)
                tanggal_selesai = datetime.strptime(selesai_str, for_parse)
                periode_str     = f"{tanggal_id(tanggal_mulai)} - {tanggal_id(tanggal_selesai)}"
            except ValueError:
                pass                            # biarkan periode_str = periode_raw

        # Buat dokumen paket
        doc = {
            'nama': nama,
            'layanan_id': ObjectId(layanan_id),
            'harga': harga,
            'deposit': deposit,
            'keuntungan': keuntungan,
            'tim_kerja': tim_kerja,
            'periode': {
                'mulai': tanggal_mulai,
                'selesai': tanggal_selesai
            },
            "status": True,   # paket aktif secara default
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
        periode = request.form['periode']

        # Parsing tanggal dari input periode
        tanggal_mulai = tanggal_selesai = None
        if periode:
            periode = periode.replace('–', ' to ').replace('—', ' to ')
            if ' to ' in periode:
                mulai_str, selesai_str = [s.strip() for s in periode.split(' to ')]
            else:
                mulai_str = selesai_str = periode.strip()

            for_parse = "%d %B %Y"
            try:
                tanggal_mulai = datetime.strptime(mulai_str, for_parse)
                tanggal_selesai = datetime.strptime(selesai_str, for_parse)
            except ValueError:
                pass  # Jika parsing gagal, biarkan tetap None

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
                'periode': {
                    'mulai': tanggal_mulai,
                    'selesai': tanggal_selesai
                },
                "status": True   # paket aktif secara default
            }

            db.paket.update_one({'_id': ObjectId(_id)}, {'$set': doc})
            return redirect(url_for('admin_paketFotografi'))

    id = ObjectId(_id)
    data = db.paket.find_one({"_id": id})
    layanan = list(db.layanan.find())

    # Format ulang periode jika ada
    periode_str = ''
    if data.get('periode') and data['periode'].get('mulai') and data['periode'].get('selesai'):
        mulai = data['periode']['mulai']
        selesai = data['periode']['selesai']
        periode_str = f"{tanggal_id(mulai)} to {tanggal_id(selesai)}"

    return render_template('admin/paketFotografi_ubah.html', data=data, layanan=layanan, paket_exists=paket_exists, periode_str=periode_str)

# User - Lihat Paket
@app.route('/lihat_paket/<layanan_id>')
def lihat_paket(layanan_id):
    # Cari layanan berdasarkan id
    layanan = db.layanan.find_one({'_id': ObjectId(layanan_id)})
    if not layanan:
        return "Layanan tidak ditemukan", 404

    # Hanya ambil paket yang aktif
    paket_list = list(db.paket.find({
        'layanan_id': ObjectId(layanan_id),
        'status': True  # hanya paket dengan status aktif
    }))

    # Pastikan setiap item punya .periode_str
    for p in paket_list:
        if not p.get("periode_str"):
            mulai   = p.get("periode", {}).get("mulai")
            selesai = p.get("periode", {}).get("selesai")
            if mulai and selesai:
                p["periode_str"] = f"{tanggal_id(mulai)} - {tanggal_id(selesai)}"
            else:
                p["periode_str"] = "Tidak ada periode"

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







# Jadwal
@app.route('/admin_jadwal')
def admin_jadwal():
    return render_template('admin/Jadwal.html')

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
    pesanan = list(db.pesanan.find())
    layanan_map = {str(l['_id']): l['nama'] for l in db.layanan.find()}

    # Tambahkan nama layanan ke dalam setiap dokumen pesanan
    for p in pesanan:
        layanan_id = str(p.get('layanan_id'))
        p['layanan'] = layanan_map.get(layanan_id, 'Tidak ditemukan')
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
            layanan_id = request.form['layanan_id']
            paket_id = request.form['paket_id']
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
            biaya_transportasi = int(biaya_transportasi_str) if biaya_transportasi_str.isdigit() else 0

            # Get total_harga and sisa_bayar from hidden fields in frontend
            total_harga = float(request.form.get('total_harga', '0'))
            sisa_bayar = float(request.form.get('sisa_bayar', '0'))


            # Konversi tanggal dan waktu
            tanggal_pemesanan = datetime.strptime(tanggal_pemesanan_str, '%Y-%m-%d')
            jam_acara = jam_acara_str
            tanggal_mulai_acara = datetime.strptime(tanggal_mulai_acara_str, '%Y-%m-%d')
            tanggal_selesai_acara = datetime.strptime(tanggal_selesai_acara_str, '%Y-%m-%d')

            # --- Recalculate costs on backend for security/validation ---
            # This is crucial as frontend calculations can be manipulated.
            # Backend should always be the source of truth for financial data.

            # Get Paket Price and Deposit
            selected_paket = db.paket.find_one({'_id': ObjectId(paket_id)})
            if not selected_paket:
                raise ValueError("Paket tidak ditemukan.")
            harga_paket = selected_paket.get('harga', 0)
            deposit_paket = selected_paket.get('deposit', 0) # Get deposit from selected package

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

            # Optional: Add a check if frontend total matches backend total (within a small tolerance)
            # if abs(recalculated_total_harga - total_harga) > 0.01:
            #     print(f"Warning: Frontend total ({total_harga}) doesn't match backend total ({recalculated_total_harga})")
            #     # You might want to raise an error or log this discrepancy

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
                'tanggal_pemesanan': tanggal_id(tanggal_pemesanan),
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
                'tanggal_mulai_acara': tanggal_id(tanggal_mulai_acara),
                'tanggal_selesai_acara': tanggal_id(tanggal_selesai_acara),
                'lokasi_luar_labuhanbatu': lokasi_luar,
                'lokasi_id': lokasi_id_db,
                'alamat_lokasi_acara': alamat_lokasi_final,
                'link_maps_acara': link_maps_final,
                'surat_izin_lokasi': surat_izin_lokasi_filename,
                'biaya_transportasi_akomodasi': biaya_transportasi,
                'biaya_tambahan_hari': biaya_tambahan_hari,
                'biaya_lokasi': biaya_lokasi,
                'harga_paket': harga_paket, # Store base package price
                'deposit': deposit_paket,   # Store calculated deposit
                'total_harga': recalculated_total_harga, # Store calculated total
                'sisa_bayar': recalculated_sisa_bayar,   # Store calculated remaining payment
                'status_pesanan': 'Menunggu Konfirmasi',
                'created_at': datetime.utcnow()
            }

            db.pesanan.insert_one(pesanan_doc)

            return redirect(url_for("admin_pesanan"))

        except Exception as e:
            print(f"Error adding order: {e}")
            layanan_list = list(db.layanan.find())
            lokasi_list = list(db.lokasi.find())
            # Convert ObjectIds to strings for template
            for layanan in layanan_list:
                layanan['_id'] = str(layanan['_id'])
            for lokasi in lokasi_list:
                lokasi['_id'] = str(lokasi['_id'])
            return render_template('admin/pesanan_tambah.html',
                                   layanan_list=layanan_list,
                                   lokasi_list=lokasi_list,
                                   error_message=f"Terjadi kesalahan: {e}")

    # If method GET, display form
    layanan_list = list(db.layanan.find())
    lokasi_list = list(db.lokasi.find())
    # Convert ObjectIds to strings for template
    for layanan in layanan_list:
        layanan['_id'] = str(layanan['_id'])
    for lokasi in lokasi_list:
        lokasi['_id'] = str(lokasi['_id'])
    return render_template('admin/pesanan_tambah.html',
                           layanan_list=layanan_list,
                           lokasi_list=lokasi_list)

@app.route('/admin_pesanan_detail')
def admin_pesanan_detail():
    pesanan = list(db.pesanan.find())

    # Buat map nama layanan, paket, dan lokasi berdasarkan _id
    layanan_map = {str(l['_id']): l['nama'] for l in db.layanan.find()}
    paket_map = {str(l['_id']): l['nama'] for l in db.paket.find()}
    lokasi_map = {str(l['_id']): l['nama'] for l in db.lokasi.find()}

    # Tambahkan nama layanan ke dalam setiap dokumen pesanan
    for p in pesanan:
        # Konversi ObjectId pesanan ke string untuk digunakan di URL/form
        p['_id'] = str(p['_id'])

        # Layanan
        layanan_id = str(p.get('layanan_id', ''))
        p['layanan'] = layanan_map.get(layanan_id, 'Tidak ditemukan')

        # Paket
        paket_id = str(p.get('paket_id', ''))
        p['paket'] = paket_map.get(paket_id, 'Tidak ditemukan')

        # Lokasi (bisa None atau kosong jika input manual)
        lokasi_id = str(p.get('lokasi_id', ''))
        if lokasi_id and lokasi_id != "None":
            p['lokasi'] = lokasi_map.get(lokasi_id, 'Tidak ditemukan')
        else:
            p['lokasi'] = '(Lokasi Manual)' if p.get('alamat_lokasi_acara') else 'Tidak tersedia'

    return render_template('admin/pesanan_detail.html', pesanan=pesanan, current_route=request.path)


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

@app.route('/admin_kirim_pengingat', methods=['POST'])
def admin_kirim_pengingat():
    email = request.form['email_klien']
    whatsapp = request.form['whatsapp_klien']
    status = request.form['status_pesanan']
    nama = request.form['nama_klien']

    # Format pesan pengingat sesuai status
    if status == 'Belum Pemotretan':
        pesan = f"Halo {nama}, ini adalah pengingat untuk jadwal pemotretan Anda bersama Oval Photo."
    elif status == 'Sudah Pemotretan':
        pesan = f"Halo {nama}, mohon melakukan pelunasan pembayaran untuk layanan fotografi Oval Photo."
    elif status == 'Sudah Kirim File & Album':
        pesan = f"Halo {nama}, semoga Anda puas. Silakan beri ulasan mengenai layanan kami di Oval Photo :)"
    else:
        pesan = f"Halo {nama}, status pesanan Anda saat ini: {status}"

    # Simulasi pengiriman WA (contoh dengan WhatsApp API)
    nomor_wa = whatsapp.replace('+', '')
    wa_url = f"https://api.whatsapp.com/send?phone={nomor_wa}&text={urllib.parse.quote(pesan)}"
    print("Opening WhatsApp link:", wa_url)

    # Kirim Email (opsional, ganti dengan fungsi real email)
    print(f"Mengirim email ke {email} dengan isi: {pesan}")

    flash("Pengingat berhasil dikirim melalui WhatsApp dan Email", "success")
    return redirect('/admin_pesanan_detail')




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


@app.route('/booking')
def booking():
    return render_template('user/booking.html')

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
