Feature: Generate Activity Diagram

  Scenario: Membuat Activity Diagram dari skenario yang ada
    Given user sudah memiliki data skenario fitur di sistem
    When user menekan tombol "Generate Activity Diagram"
    Then sistem menampilkan visualisasi Activity Diagram via PlantUML