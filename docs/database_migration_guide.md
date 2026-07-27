# Database Migration & Best Practice Guide
## One UML — SRS Generator Tools
**Versi:** 1.0 | **Tanggal:** 2026-07-24 | **Author:** System Analyst

---

## 1. Mengapa SQLite Berbahaya untuk Multi-User / Produksi?

SQLite menyimpan seluruh database dalam **satu file** (`db.sqlite3`) di filesystem server. Ini menimbulkan beberapa risiko kritis:

| Risiko | Penjelasan |
|--------|-----------|
| **Tidak mendukung concurrent writes** | Jika dua user menyimpan data bersamaan, salah satu request akan gagal atau data bisa korup |
| **File database di-share via Git** | Jika `db.sqlite3` tidak ada di `.gitignore`, seluruh isi database (termasuk data sensitif) masuk ke version control dan bisa dilihat siapapun |
| **Tidak portable** | Tidak bisa diakses dari multiple server/worker process secara bersamaan (tidak cocok untuk deploy dengan Gunicorn multi-worker) |
| **Tidak ada user isolation** | SQLite tidak punya mekanisme row-level security bawaan |

**Keputusan Arsitektur:** Aplikasi ini menggunakan **Supabase (PostgreSQL)** sebagai database produksi karena:
- Mendukung concurrent reads & writes
- Row-level security (RLS) tersedia
- Gratis tier yang cukup untuk MVP
- Connection pooling built-in (Supavisor)

---

## 2. Arsitektur Database Saat Ini

### 2.1 Entity Relationship Overview

```
Pengguna (1) ─────── (N) Project
                            │
            ┌───────────────┼───────────────┐
            │               │               │
          GUI (1)    UserStory (N)  UseCaseSpecification (N)
            │               │               │
          Page (N)   Sequences    BasicPath/AltPath/ExcPath
            │
         Element (N)
```

### 2.2 Data Isolation — Kebijakan Wajib

Setiap entitas data **wajib** memiliki relasi ke `Project` (langsung atau via FK chain). Query di view **wajib** menggunakan filter `project=active_project`.

| Model | FK ke Project | Status |
|-------|---------------|--------|
| `GUI` | Langsung (`project` FK) | ✅ |
| `UserStory` | Langsung (`project` FK) + via GUI | ✅ |
| `UseCaseSpecification` | Langsung (`project` FK) + via GUI | ✅ |
| `Feature` | Langsung (`project` FK) | ✅ |
| `SqlTable` | Langsung (`project` FK) | ✅ |
| `ImportedTable` | Langsung (`project` FK) | ✅ |
| `ActivityDiagram` | Via UseCaseSpecification → Project | ✅ |
| `Sequence` | Via UserStory → Project | ✅ |
| `ClassDiagram` | Via UserStory → Project | ✅ |

### 2.3 Database-Level Constraints (Ditambahkan v0005)

Constraint ini memastikan integritas data di level database, bukan hanya di aplikasi:

| Model | Constraint | Tujuan |
|-------|-----------|--------|
| `GUI` | `unique_gui_per_project` | Satu project hanya punya satu GUI |
| `UserStory` | `unique_userstory_per_project` | Tidak ada duplikat actor+fitur dalam satu project |
| `UseCaseSpecification` | `unique_spec_per_project` | Tidak ada duplikat feature_name dalam satu project |
| `Feature` | `unique_feature_per_project` | Tidak ada duplikat nama fitur dalam satu project |
| `ImportedTable` | `unique_together (project, name)` | Tidak ada duplikat nama tabel dalam satu project |

---

## 3. Setup Supabase (Step-by-Step)

### Prasyarat
- Akun Supabase di [supabase.com](https://supabase.com)
- Project Supabase sudah dibuat

### Langkah 3.1: Dapatkan Connection String

1. Buka Supabase Dashboard → Project kamu
2. Klik **Settings** (kiri bawah) → **Database**
3. Scroll ke bagian **Connection string**
4. Pilih tab **URI**
5. **PENTING:** Gunakan mode **Transaction (port 6543)** bukan Session (port 5432)
6. Salin connection string — formatnya:
   ```
   postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
   ```

### Langkah 3.2: Setup `.env` Lokal

```bash
# Di folder project
copy .env.example .env
```

Edit `.env` dan isi `DATABASE_URL`:
```env
DATABASE_URL=postgresql://postgres.abcdefghijk:yourpassword@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
SECRET_KEY=buat-secret-key-baru-di-sini
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Langkah 3.3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Langkah 3.4: Jalankan Migrasi Schema ke Supabase

```bash
# Verifikasi koneksi dulu
python manage.py dbshell

# Jalankan semua migrasi (ini membuat schema di Supabase)
python manage.py migrate

# Verifikasi semua migrasi applied
python manage.py showmigrations
```

### Langkah 3.5: Buat Session Table

```bash
python manage.py migrate sessions
```

---

## 4. Migration Plan (SQLite → Supabase)

### 4.1 Keputusan: Fresh Migration (Recommended)

Karena data di `db.sqlite3` lokal bersifat data development yang sudah bercampur antar project (bug data isolation yang sudah diperbaiki), **direkomendasikan fresh migration** — hanya migrasikan schema, tidak migrasikan data lama.

> [!NOTE]
> Jika kamu memiliki data production yang perlu dipreservasi, ikuti langkah 4.2. Jika ini data development saja, langsung ke langkah 3.4 sudah cukup.

### 4.2 Migrasi Data (Opsional — jika data perlu dipreservasi)

#### Backup data dari SQLite:
```bash
# Export semua data ke fixture JSON
python manage.py dumpdata --natural-foreign --natural-primary \
    --exclude auth.permission --exclude contenttypes \
    --indent 2 > backup_sqlite_$(date +%Y%m%d).json
```

#### Bersihkan data yang bermasalah (jika ada):
```python
# Script Python untuk assign ulang project_id yang benar
# Jalankan di Django shell: python manage.py shell

from main.models import UserStory, GUI, Project

# Cek data orphan (UserStory tanpa project)
orphans = UserStory.objects.filter(project__isnull=True)
print(f"Orphan UserStories: {orphans.count()}")

# Assign ke project berdasarkan GUI-nya
for us in orphans:
    if us.gui and us.gui.project:
        us.project = us.gui.project
        us.save()
        print(f"Fixed: {us}")
```

#### Import ke Supabase:
```bash
# Pastikan DATABASE_URL sudah mengarah ke Supabase
python manage.py loaddata backup_sqlite_YYYYMMDD.json
```

### 4.3 Rollback Plan

Jika migrasi ke Supabase gagal:

- [ ] **Rollback 1 — Kembali ke SQLite:** Hapus/comment `DATABASE_URL` di `.env` → otomatis pakai SQLite lokal kembali
- [ ] **Rollback 2 — Restore backup:** Kembalikan `.env` ke SQLite, jalankan `python manage.py loaddata backup_sqlite.json`
- [ ] **Rollback 3 — Revert migrasi:** Jika ada migrasi baru yang gagal: `python manage.py migrate main 0004` (rollback ke versi sebelumnya)
- [ ] **Verifikasi:** Setelah rollback, jalankan `python manage.py check` dan test alur New Project

---

## 5. Checklist Pre-Deployment

Sebelum deploy ke production dengan Supabase:

- [ ] `DEBUG=False` di `.env`
- [ ] `SECRET_KEY` sudah diganti dengan nilai yang kuat (bukan default)
- [ ] `ALLOWED_HOSTS` sudah diisi dengan domain production
- [ ] `python manage.py check --deploy` tidak ada error kritis
- [ ] `python manage.py collectstatic` sudah dijalankan
- [ ] File `.env` **tidak** ada di Git (`git status` tidak menampilkan `.env`)
- [ ] `db.sqlite3` **tidak** ada di Git (sudah di `.gitignore`)
- [ ] Semua migrasi sudah applied di Supabase (`python manage.py showmigrations`)

---

## 6. Monitoring & Maintenance

### Cek health database:
```bash
python manage.py dbshell
# Di psql: \dt — lihat semua tabel
# Di psql: SELECT COUNT(*) FROM main_project; — cek data
```

### Cek session yang expired:
```bash
python manage.py clearsessions
```

### Backup rutin Supabase:
Supabase menyediakan backup otomatis di plan Pro. Untuk free tier, export manual:
```bash
python manage.py dumpdata > backup_$(date +%Y%m%d_%H%M).json
```

---

*Dokumen ini adalah bagian dari artefak System Analysis untuk proyek One UML SRS Generator Tools.*
*Last updated: 2026-07-24*
