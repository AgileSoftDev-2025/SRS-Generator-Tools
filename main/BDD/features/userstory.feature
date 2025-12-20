Feature: User Story Input
  Scenario: Menyimpan User Story baru
    Given user berada di halaman input User Story
    When user memasukkan Actor "Pelanggan" dan Fitur "Pesan Produk"
    Then data User Story berhasil tersimpan di database