Feature: Generate Class Diagram
  Scenario: Membuat diagram dari file SQL
    Given user mengunggah file .sql ke sistem
    When SQL Parser membaca tabel dan relasi
    Then Class Diagram berhasil divisualisasikan