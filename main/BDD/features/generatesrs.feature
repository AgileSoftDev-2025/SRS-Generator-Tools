Feature: Generate SRS Document

  Scenario: Merangkum seluruh artefak menjadi dokumen SRS
    Given seluruh diagram dan spesifikasi telah selesai dibuat
    When user menekan tombol "Generate SRS Document"
    Then sistem menghasilkan file dokumen SRS dalam format PDF