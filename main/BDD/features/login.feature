Feature: Login Pengguna

  Scenario: Login dengan kredensial yang valid
    Given pengguna berada di halaman login
    When pengguna memasukkan username "anindya" dan password "password123"
    Then pengguna berhasil masuk ke dashboard utama