# library for server
from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin

# library for qr generator
import qrcode
from PIL import Image

# library for database connection
import pymysql.cursors

# library for crypto
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
import urllib.parse
import base64
from os import path

# ============================================================================
#                                 DATABASE
# ============================================================================
#   Database Configuration
#
DB_SERVER = "localhost"
DB_USERNAME = "root"
DB_PASSWORD = ""
DB_NAME = "presensi_cerdas"
#
# ============================================================================


# ============================================================================
#                                 KONFIGURASI
# ============================================================================

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

conn = cursor = None

def open_DB():
    global conn, cursor
    
    conn = pymysql.connect(DB_SERVER, DB_USERNAME, DB_PASSWORD, DB_NAME)
    cursor = conn.cursor()

def close_DB():
    global conn, cursor
    
    conn.close()
    cursor.close()

# ===========================================================================
#                             MINI DOCUMENTATION
# ===========================================================================
#
#   Client Error Code
#   400 -> Bad Request
#   401 -> Unauthorized
#   403 -> Forbidden
#   404 -> Not Found
#   405 -> Method Not Allowed
#   406 -> Not Acceptable
# 
#   Server Error Code
#   500 -> Internal Server Error
#   502 -> Bad Gateway
#   503 -> Service Unavailable
#   504 -> Gateway Timeout
#
#   Success Code
#   200 -> OK
#   201 -> Created
#   202 -> Accepted
#   204 -> No Content
#
# ===========================================================================

# ===========================================================================
#                                HELPER FUNCTION
# ===========================================================================


# *************************
# VIGENERE CIPHER THINGS
# *************************

# generateKey("contoh string", "kunci")
def generateKey(string, key): 
    key = list(key) 
    if len(string) == len(key): 
        return(key) 
    else: 
        for i in range(len(string) - 
                       len(key)): 
            key.append(key[i % len(key)]) 
    return("" . join(key)) 


def vigenere_cipher(text, key, process):
    if(process == 'encrypt'):
        cipher_text = [] 
        for i in range(len(text)): 
            x = (ord(text[i]) + 
                 ord(key[i])) % 26
            x += ord('A') 
            cipher_text.append(chr(x))
            
        return("" . join(cipher_text))
    elif(process == 'decrypt'):
        orig_text = [] 
        for i in range(len(text)): 
            x = (ord(text[i]) - 
                 ord(key[i]) + 26) % 26
            x += ord('A') 
            orig_text.append(chr(x))
            
        return("" . join(orig_text)) 
    else:
        print("proses tidak dikenali")
        return ""
    

def encrypt_data(text, keyword):
    text = text.upper()
    keyword = keyword.upper()
    
    key = generateKey(text, keyword)
    
    return vigenere_cipher(text, key, 'encrypt')

def decrypt_data(text, keyword):
    text = text.upper()
    keyword = keyword.upper()
    
    key = generateKey(text, keyword)
    
    return vigenere_cipher(text, key, 'decrypt')

# *************************
# END OF VIGENERE CIPHER THINGS
# *************************

# *************************
# RSA THINGS
# *************************

def RSA_generate_keys(key_size):
    
    # generating a key pair of public and private key for given size   
    key_pair = RSA.generate(key_size)
    
    # storing private key in file name as private_key_{keysize}.pem 
    file_obj = open("private_key_"+str(key_size)+".pem", "wb")
    file_obj.write(key_pair.exportKey('PEM'))
    file_obj.close()
    
    pubkey = key_pair.publickey()
    
    # storing public key in file name as public_key_{keysize}.pem    
    file_obj = open("public_key_"+str(key_size)+".pem", "wb")
    file_obj.write(pubkey.exportKey('OpenSSH'))
    file_obj.close()


def init_RSA_key():
    key_size = 1024
    RSA_generate_keys(key_size)

def byte_to_string(val_in_bytes):
    return val_in_bytes.decode()
    
def string_to_byte(val_as_string):
    return val_as_string.encode()
    
def quote_string(unquoted_string):
    return urllib.parse.quote(unquoted_string)

def unquote_string(quoted_string):
    return urllib.parse.unquote(quoted_string)

def RSA_encrypt(message, public_key_pem_path):    
    # set public key path 
    public_key_path = '/public_key_1024.pem'

    loaded = False    
    
    while not loaded:
        try:
            public_key = RSA.importKey(open(public_key_path, 'r').read())
            
            if public_key:
                loaded = True
            else:
                print('Initialize Public Key*')
                init_RSA_key()
        except:
            print('Initialize Public Key')
            init_RSA_key()
    
    # creating the RSA object using public key
    rsa_object = PKCS1_v1_5.new(public_key)
    cipher_text = rsa_object.encrypt(message.encode())
    cipher_text = base64.b64encode(cipher_text)
    
    return cipher_text
    

# *************************
# END OF RSA THINGS
# *************************

def generate_QR(url):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    
    filename = 'sample.png'

    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(
        fill_color="black", 
        back_color="white"
        ).convert('RGB')
    
    img.save(filename)
    
    return filename

# ===========================================================================
#                                   BATAS SUCI
# ===========================================================================

@cross_origin()
@app.route('/', methods=['POST'])
def index():
    
    message = "Request Salah"
    status = "Method Not Allowed"
    code = 403
    
    if request.method == 'POST':
        user_request = request.get_json()
        
        message = user_request['nama']
        status = 'OK'
        code = 200
        
        print(user_request)
    
    data = {"message": message, "status": status, "code": code}
    
    return jsonify(data)

# *************************
# MAHASISWA THINGS
# *************************

@cross_origin()
@app.route('/mahasiswa', methods=['GET'])
@app.route('/mahasiswa/<nim>', methods=['GET'])
@app.route('/mahasiswa/<nim_presensi>/presensi', methods=['GET'])
def mahasiswa(nim = 0, nim_presensi = 0):
    open_DB()
    
    container = []
    status = 'No Content'
    code = 204
    
    if nim == 0:
        sql = "SELECT * FROM mahasiswa";
        cursor.execute(sql)
        results = cursor.fetchall()
        
        mhs = list()
        for r in results:
            mhs.append(r)
        
        if len(mhs) > 0:
            container.append(mhs)
            
    elif nim_presensi != 0:
        sql = "SELECT presensi.Id_presensi as id_presensi, presensi.Id_jadwal as id_jadwal, presensi.Pertemuan as pertemuan, presensi.Tanggal_jam_publish as tanggal_jam_publish, presensi.Tanggal_jam_presensi, jadwal.Id_jadwal as id_jadwal, jadwal.Hari as hari, jadwal.Jam as jam, kelas.Id_kelas as id_kelas, matakuliah.Id_matkul as id_matkul, matakuliah.nama as nama_matakuliah, dosen.NIP, dosen.Nama as nama_dosen, dosen.Prodi as prodi FROM jadwal JOIN presensi ON presensi.Id_jadwal = jadwal.Id_jadwal JOIN kelas ON kelas.Id_kelas = jadwal.Id_kelas JOIN matakuliah ON matakuliah.Id_matkul = jadwal.Id_matkul JOIN dosen ON dosen.NIP = kelas.NIP WHERE presensi.NIM=%s"
        val = (nim_presensi)
        cursor.execute(sql, val)
        results = cursor.fetchall()
        
        mhs = list()
        for r in results:
            mhs.append(r)
        
        if len(mhs) > 0:
            container.append(mhs)
        
    else:
        sql = "SELECT * FROM mahasiswa WHERE NIM=%s"
        val = (nim)
        cursor.execute(sql, val)
        mhs = cursor.fetchone()
        
        if mhs:
            container.append(mhs)
    
    close_DB()
    
    if container:
        status = 'OK'
        code = 200
    
    data = {'data': container, 'status': status, 'code': code}
    
    return jsonify(data)

# *************************
# END OF MAHASISWA THINGS
# *************************


# *************************
# MATAKULIAH THINGS
# *************************

@cross_origin()
@app.route('/matakuliah', methods=['GET'])
@app.route('/matakuliah/<id>', methods=['GET'])
@app.route('/matakuliah/<id_jadwal>/jadwal', methods=['GET'])
def matakuliah(id = 0, id_jadwal = 0):
    open_DB()
    
    container = []
    status = 'No Content'
    code = 204
    
    if id == 0:
        sql = "SELECT * FROM matakuliah";
        cursor.execute(sql)
        results = cursor.fetchall()
        
        matkul = list()
        for r in results:
            matkul.append(r)
        
        if len(matkul) > 0:
            container.append(matkul)
    
    elif id_jadwal != 0:
        print('debug berjalan')
        
        sql = "SELECT matakuliah.Id_matkul as id_matkul, matakuliah.Nama as nama_matkul, kelas.Id_kelas as id_kelas, dosen.NIP, dosen.Nama as nama_dosen, dosen.Prodi as prodi, jadwal.Id_jadwal as id_jadwal, jadwal.Hari as hari, jadwal.Jam as jam FROM kelas JOIN jadwal ON kelas.Id_kelas = jadwal.Id_kelas JOIN dosen ON dosen.NIP = kelas.NIP JOIN matakuliah ON matakuliah.Id_matkul = kelas.Id_matkul WHERE matakuliah.Id_matkul=%s"
        val = (id_jadwal)
        cursor.execute(sql, val)
        results = cursor.fetchall()
        
        matkul = list()
        for r in results:
            matkul.append(r)
        
        if len(matkul) > 0:
            container.append(matkul)
            
    else:
        sql = "SELECT * FROM matakuliah WHERE Id_matkul=%s"
        val = (id)
        cursor.execute(sql, val)
        matkul = cursor.fetchone()
        
        if matkul:
            container.append(matkul)
    
    close_DB()
    
    if container:
        status = 'OK'
        code = 200
    
    data = {'data': container, 'status': status, 'code': code}
    
    return jsonify(data)


@cross_origin()
@app.route('/jadwal', methods=['GET'])
@app.route('/jadwal/<id>', methods=['GET'])
def jadwal(id = 0):
    open_DB()
    
    container = []
    status = 'No Content'
    code = 204
    
    if id == 0:
        sql = "SELECT * FROM jadwal";
        cursor.execute(sql)
        results = cursor.fetchall()
        
        sch = list()
        for r in results:
            sch.append(r)
        
        if len(sch) > 0:
            container.append(sch)
            
    else:
        sql = "SELECT * FROM jadwal WHERE Id_jadwal=%s"
        val = (id)
        cursor.execute(sql, val)
        sch = cursor.fetchone()
        
        if sch:
            container.append(sch)
    
    close_DB()
    
    if container:
        status = 'OK'
        code = 200
    
    data = {'data': container, 'status': status, 'code': code}
    
    return jsonify(data)


@cross_origin()
@app.route('/kelas', methods=['GET'])
@app.route('/kelas/<id>', methods=['GET'])
@app.route('/kelas/<id_jadwal>/jadwal', methods=['GET'])
def kelas(id = 0, id_jadwal = 0):
    open_DB()
    
    container = []
    status = 'No Content'
    code = 204
    
    if id == 0:
        sql = "SELECT * FROM kelas";
        cursor.execute(sql)
        results = cursor.fetchall()
        
        kls = list()
        for r in results:
            kls.append(r)
        
        if len(kls) > 0:
            container.append(kls)
        
    elif id_jadwal != 0:
        print('debug berjalan')
        
        sql = "SELECT matakuliah.Id_matkul as id_matkul, matakuliah.Nama as nama_matkul, kelas.Id_kelas as id_kelas, dosen.NIP, dosen.Nama as nama_dosen, dosen.Prodi as prodi, jadwal.Id_jadwal as id_jadwal, jadwal.Hari as hari, jadwal.Jam as jam FROM kelas JOIN jadwal ON kelas.Id_kelas = jadwal.Id_kelas JOIN dosen ON dosen.NIP = kelas.NIP JOIN matakuliah ON matakuliah.Id_matkul = kelas.Id_matkul WHERE kelas.Id_kelas=%s"
        val = (id_jadwal)
        cursor.execute(sql, val)
        kls = cursor.fetchone()
        
        if kls:
            container.append(kls)
            
    else:
        sql = "SELECT * FROM kelas WHERE Id_kelas=%s"
        val = (id)
        cursor.execute(sql, val)
        kls = cursor.fetchone()
        
        if kls:
            container.append(kls)
    
    close_DB()
    
    if container:
        status = 'OK'
        code = 200
    
    data = {'data': container, 'status': status, 'code': code}
    
    return jsonify(data)

# *************************
# END OF MATAKULIAH THINGS
# *************************


# *************************
# DOSEN THINGS
# *************************

@cross_origin()
@app.route('/dosen', methods=['GET'])
@app.route('/dosen/<nip>', methods=['GET'])
@app.route('/dosen/<id_jadwal>/jadwal', methods=['GET'])
def dosen(nip = 0, id_jadwal = 0):
    open_DB()
    
    container = []
    status = 'No Content'
    code = 204
    
    if nip == 0:
        sql = "SELECT * FROM dosen";
        cursor.execute(sql)
        results = cursor.fetchall()
        
        dsn = list()
        for r in results:
            dsn.append(r)
        
        if len(dsn) > 0:
            container.append(dsn)
    
    elif id_jadwal != 0:
        print('debug berjalan')
        
        sql = "SELECT matakuliah.Id_matkul as id_matkul, matakuliah.Nama as nama_matkul, kelas.Id_kelas as id_kelas, dosen.NIP, dosen.Nama as nama_dosen, dosen.Prodi as prodi, jadwal.Id_jadwal as id_jadwal, jadwal.Hari as hari, jadwal.Jam as jam FROM kelas JOIN jadwal ON kelas.Id_kelas = jadwal.Id_kelas JOIN dosen ON dosen.NIP = kelas.NIP JOIN matakuliah ON matakuliah.Id_matkul = kelas.Id_matkul WHERE dosen.NIP=%s"
        val = (id_jadwal)
        cursor.execute(sql, val)
        results = cursor.fetchall()
        
        dsn = list()
        for r in results:
            dsn.append(r)
        
        if len(dsn) > 0:
            container.append(dsn)
            
    else:
        sql = "SELECT * FROM dosen WHERE NIP=%s"
        val = (nip)
        cursor.execute(sql, val)
        dsn = cursor.fetchone()
        
        if dsn:
            container.append(dsn)
    
    close_DB()
    
    if container:
        status = 'OK'
        code = 200
    
    data = {'data': container, 'status': status, 'code': code}
    
    return jsonify(data)

# *************************
# END OF DOSEN THINGS
# *************************


@cross_origin()
@app.route('/about', methods=['GET'])
def about():

    message = "Aplikasi ini berjalan pada flask dengan program versi alpha"
    status = "OK"
    code = 200

    data = {"message": message, "status": status, "code": code}

    return jsonify(data)