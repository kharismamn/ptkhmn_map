import os
import sys
import glob
import base64
import requests
from datetime import datetime

BREVO_API_KEY = os.getenv('BREVO_API_KEY')
SENDER_EMAIL = os.getenv('SENDER_EMAIL')  # Email pengirim yang terverifikasi di Brevo
SENDER_NAME = os.getenv('SENDER_NAME', 'Tim Baja Jabodetabek')
RECIPIENTS_FILE = 'recipients.txt'

def get_latest_excel():
    """Mencari file Excel paling baru yang di-generate oleh scraper"""
    files = glob.glob('Data_Baja_Konstruksi_*.xlsx')
    if not files:
        return None
    # Urutkan berdasarkan waktu modifikasi terbaru
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]

def load_recipients():
    """Membaca daftar email penerima dari file recipients.txt"""
    if not os.path.exists(RECIPIENTS_FILE):
        print(f"Error: File {RECIPIENTS_FILE} tidak ditemukan!")
        return []
    with open(RECIPIENTS_FILE, 'r') as f:
        emails = [
            line.strip() for line in f 
            if line.strip() and not line.strip().startswith('#') and '@' in line
        ]
    return emails

def send_email_via_brevo():
    # 1. Validasi GitHub Secrets
    if not BREVO_API_KEY or not SENDER_EMAIL:
        print("Error: BREVO_API_KEY dan SENDER_EMAIL belum disetel di GitHub Secrets!")
        sys.exit(1)

    # 2. Validasi File Excel Lampiran
    excel_file = get_latest_excel()
    if not excel_file:
        print("Error: Tidak ada file Excel (Data_Baja_Konstruksi_*.xlsx) yang ditemukan di repositori!")
        sys.exit(1)

    # 3. Validasi Daftar Penerima
    recipients = load_recipients()
    if not recipients:
        print(f"Error: File {RECIPIENTS_FILE} kosong atau tidak ada email valid.")
        sys.exit(1)

    print(f"Mempersiapkan pengiriman file '{excel_file}' ke {len(recipients)} konsumen via Brevo...")

    # Encode file Excel ke base64
    with open(excel_file, 'rb') as f:
        file_content = base64.b64encode(f.read()).decode('utf-8')

    # Format daftar penerima sesuai spesifikasi Brevo REST API
    to_list = [{"email": email} for email in recipients]

    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }

    today_str = datetime.now().strftime("%d %B %Y")
    payload = {
        "sender": {
            "name": SENDER_NAME,
            "email": SENDER_EMAIL
        },
        "to": to_list,
        "subject": f"Data Perusahaan Baja & Konstruksi Jabodetabek Terbaru - {today_str}",
        "htmlContent": f"""
            <h2>Halo,</h2>
            <p>Berikut kami kirimkan lampiran file Excel data terbaru <b>Perusahaan Baja &amp; Konstruksi di Jabodetabek</b> untuk hari ini ({today_str}).</p>
            <p>File terlampir dapat langsung diunduh dan dibuka menggunakan Microsoft Excel atau Google Sheets.</p>
            <br>
            <p>Salam hangat,<br><b>{SENDER_NAME}</b></p>
        """,
        "attachment": [
            {
                "content": file_content,
                "name": os.path.basename(excel_file)
            }
        ]
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code in [200, 201, 202]:
            print(f"SELESAI! Email berhasil dikirim ke {len(recipients)} konsumen.")
            print("Response Brevo:", response.json())
        else:
            print(f"GAGAL MENGIRIM! Status Code: {response.status_code}")
            print("Detail Error dari Brevo:", response.text)
            sys.exit(1)
    except Exception as e:
        print(f"Terjadi kesalahan koneksi ke Brevo API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    send_email_via_brevo()
