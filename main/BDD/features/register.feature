Feature: Registrasi Pengguna

  Scenario: Mendaftarkan akun baru
    Given pengguna baru membuka halaman registrasi
    When pengguna mengisi nama "Anindya", email "anin@email.com", dan password
    Then akun berhasil dibuat dan tersimpan di database