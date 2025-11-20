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
    hasil_usecase = models.ImageField(upload_to='usecases/')

# Tabel UserStory
class UserStory(models.Model):
    id_userstory = models.CharField(max_length=5, primary_key=True)
    gui = models.ForeignKey(GUI, on_delete=models.CASCADE, related_name='userstories')
    input_sebagai = models.CharField(max_length=100)
    input_fitur = models.CharField(max_length=100)

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
class UseCaseSpecification(models.Model):
    id_usecasespecification = models.CharField(max_length=5, primary_key=True)

    # relasi ke Usecase (punya kamu sebelumnya)
    usecase = models.ForeignKey(
        Usecase, 
        on_delete=models.CASCADE, 
        related_name='specifications'
    )

    # gambar hasil
    hasil_usecasespecification = models.ImageField(upload_to='usecase_specs/')

    # Summary Description
    summary_description = models.CharField(max_length=500)

    # Priority
    PRIORITY_CHOICES = [
        ('Must Have', 'Must Have'),
        ('Should Have', 'Should Have'),
        ('Could Have', 'Could Have'),
        ("Won't Have", "Won't Have"),
    ]
    priority = models.CharField(max_length=250, choices=PRIORITY_CHOICES)

    # Status
    STATUS_CHOICES = [
        ('active', 'active'),
        ('inactive', 'inactive')
    ]
    status = models.CharField(max_length=250, choices=STATUS_CHOICES)

    # Pre & Post Condition
    input_precondition = models.CharField(max_length=500)
    input_postcondition = models.CharField(max_length=500)

    def __str__(self):
        return self.id_usecasespecification
class BasicPath(models.Model):
    usecase_spec = models.ForeignKey(
        UseCaseSpecification,
        on_delete=models.CASCADE,
        related_name='basic_paths'
    )
    step_number = models.IntegerField()
    description = models.CharField(max_length=500)

    def __str__(self):
        return f"Basic Step {self.step_number}"


class AlternativePath(models.Model):
    usecase_spec = models.ForeignKey(
        UseCaseSpecification,
        on_delete=models.CASCADE,
        related_name='alternative_paths'
    )
    related_basic_step = models.IntegerField()
    description = models.CharField(max_length=500)

    def __str__(self):
        return f"Alternative tied to Step {self.related_basic_step}"


class ExceptionPath(models.Model):
    usecase_spec = models.ForeignKey(
        UseCaseSpecification,
        on_delete=models.CASCADE,
        related_name='exception_paths'
    )
    related_basic_step = models.IntegerField()
    description = models.CharField(max_length=500)

    def __str__(self):
        return f"Exception tied to Step {self.related_basic_step}"


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
    id_activity = models.CharField(max_length=5, primary_key=True)
    scenario = models.ForeignKey(UserStoryScenario, on_delete=models.CASCADE, related_name='activities')
    script_activity = models.TextField()
    nama_usecase = models.TextField()
    main_flow = models.TextField()
    alternative_flow = models.TextField()
    hasil_activity = models.ImageField(upload_to='activities/')
