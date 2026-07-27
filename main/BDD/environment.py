import os
import django

# Beri tahu Behave di mana lokasi file settings Django kamu
# Pastikan "core.settings" sesuai dengan nama folder settings kamu (biasanya 'core' atau 'srsgenerator')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# Inisialisasi Django agar model dan aplikasi bisa terbaca
django.setup()

def before_all(context):
    """
    Fungsi ini berjalan sekali sebelum semua tes dimulai.
    Bisa digunakan untuk setup data awal jika diperlukan.
    """
    pass