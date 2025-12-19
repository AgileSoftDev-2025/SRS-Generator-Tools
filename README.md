# ⚡ One UML - SRS Generator Tools

**One UML** adalah alat bantu otomatis berbasis web yang dibangun dengan framework **Django** untuk menghasilkan dokumen *Software Requirements Specification* (SRS) secara komprehensif. Aplikasi ini mengintegrasikan pemetaan aktor, fitur, dan berbagai diagram UML ke dalam satu dokumen siap cetak.

## 🚀 Fitur Utama

1.  **Actor & Feature Mapping**: Mendefinisikan aktor sistem dan fungsionalitas utama secara dinamis.
2.  **Automated Use Case Diagram**: Menghasilkan diagram Use Case secara otomatis menggunakan integrasi PlantUML.
3.  **Sequence & Class Diagram Generator**: Membuat visualisasi alur logika dan arsitektur data dari input User Story dan file SQL.
4.  **SQL Parser & Data Dictionary**: Mengimpor file `.sql` untuk diubah menjadi tabel kamus data otomatis.
5.  **SRS Document Preview**: Tampilan preview dokumen format A4 yang rapi dan siap ekspor ke PDF.

## 🛠️ Tech Stack

* **Backend**: Python 3.12, Django Framework.
* **Frontend**: HTML5, CSS3 (Modern UI/UX), JavaScript.
* **Database**: SQLite.
* **Diagram Engine**: PlantUML & Kroki.io API.

## 💻 Cara Instalasi

1.  **Clone Repositori**
    ```bash
    git clone [https://github.com/AgileSoftDev-2025/SRS-Generator-Tools.git](https://github.com/AgileSoftDev-2025/SRS-Generator-Tools.git)
    cd SRS-Generator-Tools
    ```

2.  **Install Dependensi**
    Pastikan kamu sudah menginstal Python, lalu jalankan:
    ```bash
    pip install django requests
    ```

3.  **Persiapan Database & Media**
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

4.  **Jalankan Server**
    ```bash
    python manage.py runserver
    ```
    Buka `http://127.0.0.1:8000` di browser kamu.

## ⚠️ Catatan Penting (Troubleshooting)

* **Error `_curses`**: Jika muncul `ModuleNotFoundError: No module named '_curses'`, pastikan tidak ada baris `from curses import newpad` di bagian atas file `views.py` (khusus pengguna Windows).
* **Merge Conflict `db.sqlite3`**: Jangan mengunggah file database ke GitHub. Gunakan `.gitignore` untuk mengecualikan file `.sqlite3` agar tidak terjadi bentrokan data antar anggota tim.
* **Folder Media**: Pastikan folder `media/usecases/`, `media/sequences/`, dan `media/class_diagrams/` tersedia agar gambar diagram bisa tersimpan dengan benar.

## 📖 Alur Penggunaan

1.  **Login/Register**: Masuk ke akun pengguna.
2.  **Define Actors**: Masukkan daftar aktor dan fitur yang ingin dibuat.
3.  **Generate Diagrams**: Buka halaman Use Case, Sequence, dan Class Diagram, lalu klik tombol **Generate** untuk memproses gambar.
4.  **Print SRS**: Masuk ke halaman **Generate SRS** dan klik **Print to PDF** untuk mengambil dokumen laporan akhir.

---
© 2025 AgileSoftDev Team - One UML Project.