from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password

# Tabel Pengguna
class Pengguna(models.Model):
    id_user = models.CharField(max_length=5, primary_key=True)
    nama_user = models.CharField(max_length=100)
    email_user = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=255)

    def set_password(self, raw_password):  
        """Hash password sebelum disimpan"""
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        """Cek apakah password benar"""
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.nama_user

# Tabel Project
class Project(models.Model):
    id_project = models.CharField(max_length=5, primary_key=True)
    nama_project = models.CharField(max_length=100)
    deskripsi = models.CharField(max_length=100, blank=True)
    tanggal_project_dibuat = models.DateTimeField(default=timezone.now)
    tanggal_akses_terakhir = models.DateTimeField(default=timezone.now)
    pengguna = models.ForeignKey(Pengguna, on_delete=models.CASCADE, related_name='projects')

    def __str__(self):
        return self.nama_project

# Tabel Session
class Session(models.Model):
    id_session = models.CharField(max_length=5, primary_key=True)
    pengguna = models.ForeignKey(Pengguna, on_delete=models.CASCADE, related_name='sessions')
    login_time = models.DateTimeField()
    logout_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=False)

# Tabel GUI
class GUI(models.Model):
    id_gui = models.CharField(max_length=5, primary_key=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='guis')
    nama_atribut = models.CharField(max_length=50)

# Tabel Usecase
class Usecase(models.Model):
    id_usecase = models.AutoField(primary_key=True)
    gui = models.ForeignKey(GUI, on_delete=models.CASCADE, related_name='usecases')
    
    # simpan gambar
    hasil_usecase = models.ImageField(upload_to='usecases/')
    
    # simpan kode PlantUML
    plantuml_code = models.TextField(null=True, blank=True) 

    def __str__(self):
        return f"Use Case - {self.gui.nama_atribut}"

# Tabel UserStory
class UserStory(models.Model):
    id_userstory = models.AutoField(primary_key=True)
    gui = models.ForeignKey(GUI, on_delete=models.CASCADE, related_name='userstories')
    input_sebagai = models.CharField(max_length=100)
    input_fitur = models.CharField(max_length=100)
    input_tujuan = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        # Kalau ada tujuannya, tambahin "so that..."
        tujuan_text = f", so that {self.input_tujuan}" if self.input_tujuan else ""
        return f"As a {self.input_sebagai}, I want to {self.input_fitur}{tujuan_text}."

# Tabel UserStoryScenario
class UserStoryScenario(models.Model):
    id_scenario = models.CharField(max_length=100, primary_key=True)
    userstory = models.ForeignKey(UserStory, on_delete=models.CASCADE, related_name='scenarios')
    nama_scenario = models.TextField()
    input_given = models.TextField()
    input_when = models.TextField()
    input_then = models.TextField()
    input_and = models.TextField()

# Tabel UseCaseSpecification
# main/models.py

# ... (Model Pengguna, Project, GUI, Usecase biarkan saja) ...

# UPDATE BAGIAN INI 👇

class UseCaseSpecification(models.Model):
    # Kita ganti PK jadi AutoField biar gampang
    id = models.AutoField(primary_key=True) 
    
    # Kita sambungin ke GUI (Project), bukan ke Usecase Diagram
    # Kenapa? Karena Spek ini dibuat sebelum diagram jadi pun bisa.
    gui = models.ForeignKey(GUI, on_delete=models.CASCADE, related_name='specifications')
    
    # Tambah kolom Nama Fitur (PENTING!)
    feature_name = models.CharField(max_length=255, default="Feature")
    
    summary_description = models.TextField(null=True, blank=True)
    
    PRIORITY_CHOICES = [
        ('Must Have', 'Must Have'),
        ('Should Have', 'Should Have'),
        ('Could Have', 'Could Have'),
        ("Won't Have", "Won't Have"),
    ]
    priority = models.CharField(max_length=50, choices=PRIORITY_CHOICES, default='Must Have')
    
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive')
    ]
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Active')
    
    input_precondition = models.TextField(null=True, blank=True)
    input_postcondition = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Spec: {self.feature_name}"


# UPDATE TABEL JALUR (Biar bisa nampung Actor & System) 👇

class BasicPath(models.Model):
    usecase_spec = models.ForeignKey(UseCaseSpecification, on_delete=models.CASCADE, related_name='basic_paths')
    step_number = models.IntegerField()
    
    # Ganti description jadi 2 kolom ini biar sesuai HTML
    actor_action = models.TextField(null=True, blank=True)
    system_response = models.TextField(null=True, blank=True)

class AlternativePath(models.Model):
    usecase_spec = models.ForeignKey(UseCaseSpecification, on_delete=models.CASCADE, related_name='alternative_paths')
    step_number = models.IntegerField() # Ini buat nyimpen urutan baris
    
    actor_action = models.TextField(null=True, blank=True)
    system_response = models.TextField(null=True, blank=True)

class ExceptionPath(models.Model):
    usecase_spec = models.ForeignKey(UseCaseSpecification, on_delete=models.CASCADE, related_name='exception_paths')
    step_number = models.IntegerField()
    
    actor_action = models.TextField(null=True, blank=True)
    system_response = models.TextField(null=True, blank=True)
    

# Tabel ImportedTable
class ImportedTable(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

# Tabel ImportedColumn
class ImportedColumn(models.Model):
    table = models.ForeignKey(ImportedTable, on_delete=models.CASCADE, related_name='columns')
    name = models.CharField(max_length=255)
    data_type = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.table.name}.{self.name}"

# tabel ImportedRelationship
class ImportedRelationship(models.Model):
    table = models.ForeignKey(ImportedTable, on_delete=models.CASCADE, related_name='foreign_keys')
    column_name = models.CharField(max_length=255)
    ref_table = models.ForeignKey(ImportedTable, on_delete=models.CASCADE, related_name='referenced_by')
    ref_column_name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.table.name}.{self.column_name} → {self.ref_table.name}.{self.ref_column_name}"

# main/models.py
from django.db import models

class Feature(models.Model):
    nama = models.CharField(max_length=200)

    def __str__(self):
        return self.nama


# tabel saved SQL Table
class SqlTable(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# tabel saved SQL Column
class SqlColumn(models.Model):
    id = models.AutoField(primary_key=True)
    table = models.ForeignKey(SqlTable, on_delete=models.CASCADE, related_name='columns')
    name = models.CharField(max_length=100)
    datatype = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name} ({self.datatype})"


# Tabel Sequence
class Sequence(models.Model):
    id_sequence = models.CharField(max_length=5, primary_key=True)
    userstory = models.ForeignKey(UserStory, on_delete=models.CASCADE, related_name='sequences')
    input_actor = models.TextField()
    input_boundary = models.TextField()
    input_controller = models.TextField()
    input_entity = models.TextField()
    hasil_sequence = models.ImageField(upload_to='sequences/')

# Tabel ClassDiagram
class ClassDiagram(models.Model):
    id_classdiagram = models.CharField(max_length=5, primary_key=True)
    userstory = models.ForeignKey(UserStory, on_delete=models.CASCADE, related_name='class_diagrams')
    script_classdiagram = models.TextField()
    hasil_classdiagram = models.ImageField(upload_to='class_diagrams/')

# Tabel ActivityDiagram
class ActivityDiagram(models.Model):
    use_case_spec = models.OneToOneField(UseCaseSpecification, on_delete=models.CASCADE, related_name='activity_diagram', null=True, blank=True)
    plantuml_code = models.TextField(blank=True, default='')
    diagram_image_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Activity Diagram"
        verbose_name_plural = "Activity Diagrams"
    
    def __str__(self):
        if self.use_case_spec:
            return f"Activity Diagram for {self.use_case_spec.id_usecasespecification}"
        return "Activity Diagram (No Use Case)"
    
class Page(models.Model):
    gui = models.ForeignKey(GUI, on_delete=models.CASCADE, related_name='pages')
    name = models.CharField(max_length=255)
    order = models.PositiveIntegerField()
    
    class Meta:
        unique_together = ('gui', 'order')
        ordering = ['order']
    
    def __str__(self):
        return f"{self.name} (Page {self.order})"

class Element(models.Model):
    INPUT_TYPES = [
        ("button", "Button"),
        ("text", "Text"),
        ("number", "Number"),
        ("date", "Date"),
        ("checkbox", "Checkbox"),
        ("radio", "Radio"),
        ("textarea", "Textarea"),
    ]

    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='elements')
    name = models.CharField(max_length=255)
    input_type = models.CharField(max_length=20, choices=INPUT_TYPES)
    order = models.PositiveIntegerField()
    element_type = models.CharField(max_length=50, default="text")  # baru, bisa diisi default

    class Meta:
        db_table = 'main_inputelement'  # pastiin nyambung sama tabel SQLite lama
        unique_together = ('page', 'order')

    def __str__(self):
        return f"{self.name} ({self.input_type})"
    
    
