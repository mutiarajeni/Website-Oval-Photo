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

# Koneksi ke database MongoDB
connection_string = "mongodb+srv://test:sparta@cluster0.9kunvma.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(connection_string)
db = client.dbfotografi

app = Flask(__name__)

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
        # Server tak punya locale Indonesia? Pakai default EN lalu ganti manual.
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
@app.route('/admin_pesanan')
def admin_pesanan():
    return render_template('admin/Pesanan.html')

@app.route('/admin_pesanan_tambah')
def admin_pesanan_tambah():
    return render_template('admin/pesanan_tambah.html')

@app.route('/admin_pesanan_detail')
def admin_pesanan_detail():
    return render_template('admin/pesanan_detail.html')








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
