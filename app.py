from flask import Flask, request, render_template, redirect, url_for, session, flash, jsonify
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta
import time
from bson.objectid import ObjectId
import random
import string
import os

# Koneksi ke database MongoDB
connection_string = "mongodb+srv://test:sparta@cluster0.9kunvma.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(connection_string)
db = client.dbfotografi

app = Flask(__name__)

# Route untuk halaman user
@app.route('/')
def beranda():
    return render_template('user/beranda.html')










# User - Katalog Layanan
@app.route('/katalog_layanan')
def katalog_layanan():
    layanan = list(db.layanan.find())
    return render_template('user/katalog_layanan.html',
layanan=layanan, current_route=request.path)

# Admin - Layanan Fotografi
@app.route('/admin_layananFotografi')
def admin_layananFotografi():
    layanan = list(db.layanan.find())
    return render_template('admin/layananFotografi.html',
layanan=layanan, current_route=request.path)


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
            if gambar:
                nama_file_asli = gambar.filename
                nama_file_gambar = nama_file_asli.split('/')[-1]
                file_path = f'static/images/imgLayanan/{nama_file_gambar}'
                gambar.save(file_path)
            else:
                nama_file_gambar = None
            
            doc = {
                'nama':nama,
                'gambar': nama_file_gambar,
                'deskripsi': deskripsi
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

@app.route('/admin_layananFotografi_ubah')
def admin_layananFotografi_ubah():
    return render_template('admin/layananFotografi_ubah.html')










# Admin - Paket Fotografi
@app.route('/admin_paketFotografi')
def admin_paketFotografi():
    paket=list(db.paket.find())
    return render_template('admin/paketFotografi.html',
paket=paket, current_route=request.path)


@app.route('/admin_paketFotografi_tambah', methods=['GET','POST'])
def admin_paketFotografi_tambah():
    paket_exists=False
    
    if request.method=='POST':
        nama = request.form['nama']
        layanan_id = request.form['layanan']
        harga = int(request.form['harga'])
        deposit = int(request.form['deposit'])
        deskripsi = request.form['deskripsi']
        tim_kerja = request.form['tim_kerja']
        periode = request.form['periode']

        # Periksa apakah nama paket sudah ada
        # Parsing tanggal dari periode
        tanggal_mulai = tanggal_selesai = None
        if ' to ' in periode:
            tanggal_mulai_str, tanggal_selesai_str = periode.split(' to ')
        else:
            tanggal_range = periode.split('–')  # fallback jika memakai strip panjang
            if len(tanggal_range) == 2:
                tanggal_mulai_str, tanggal_selesai_str = tanggal_range
            else:
                tanggal_mulai_str = tanggal_selesai_str = periode

        try:
            tanggal_mulai = datetime.datetime.strptime(tanggal_mulai_str.strip(), "%d %B %Y")
            tanggal_selesai = datetime.datetime.strptime(tanggal_selesai_str.strip(), "%d %B %Y")
        except Exception as e:
            print("Error parsing date:", e)

        # Buat dokumen paket
        doc = {
            'nama': nama,
            'layanan_id': ObjectId(layanan_id),
            'harga': harga,
            'deposit': deposit,
            'deskripsi': deskripsi,
            'tim_kerja': tim_kerja,
            'periode': {
                'mulai': tanggal_mulai,
                'selesai': tanggal_selesai
            },
            'created_at': datetime.datetime.utcnow()
        }
        db.paket.insert_one(doc)
        return redirect(url_for("admin_paketFotografi"))
    return render_template('admin/paketFotografi_tambah.html', paket_exists=paket_exists)


@app.route('/admin_paketFotografi_ubah')
def admin_paketFotografi_ubah():
    return render_template('admin/paketFotografi_ubah.html')


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
    












@app.route('/jadwal')
def jadwal():
    return render_template('user/jadwal.html')

@app.route('/engagement')
def engagement():
    return render_template('user/paket_engagement.html')

@app.route('/prewedding')
def prewedding():
    return render_template('user/paket_prewedding.html')

@app.route('/wedding')
def wedding():
    return render_template('user/paket_wedding.html')


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

@app.route('/galeri')
def galeri():
    return render_template('user/galeri.html')

@app.route('/profil')
def profil_user():
    return render_template('user/profil_user.html')

@app.route('/tentang-kami')
def tentang_kami():
    return render_template('user/tentang_kami.html')

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






# Route untuk halaman admin
@app.route('/admin_dashboard')
def admin_dashboard():
    return render_template('admin/dashboard.html')







# Galeri
@app.route('/admin_galeri')
def admin_galeri():
    return render_template('admin/galeri.html')

@app.route('/admin_galeri_tambah')
def admin_galeri_tambah():
    return render_template('admin/galeri_tambah.html')

@app.route('/admin_galeri_ubah')
def admin_galeri_ubah():
    return render_template('admin/galeri_ubah.html')

# Lokasi
@app.route('/admin_lokasi')
def admin_lokasi():
    return render_template('admin/lokasi.html')

@app.route('/admin_lokasi_tambah')
def admin_lokasi_tambah():
    return render_template('admin/lokasi_tambah.html')

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

# Tim Fotografi
@app.route('/admin_timFotografi')
def admin_timFotografi():
    return render_template('admin/timFotografi.html')

@app.route('/admin_timFotografi_tambah')
def admin_timFotografi_tambah():
    return render_template('admin/timFotografi_tambah.html')

@app.route('/admin_timFotografi_ubah')
def admin_timFotografi_ubah():
    return render_template('admin/timFotografi_ubah.html')

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


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
