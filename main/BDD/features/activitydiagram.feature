Feature: Generate Use Case Diagram
  Scenario: Membuat diagram dari User Story yang ada
    Given sudah terdapat data User Story di sistem
    When user menekan tombol Generate Use Case
    Then sistem menampilkan gambar diagram via PlantUML