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
    usecase = models.ForeignKey(Usecase, on_delete=models.CASCADE, related_name='specifications')
    hasil_usecasespecification = models.ImageField(upload_to='usecase_specs/')
    input_precondition = models.TextField()
    input_postcondition = models.TextField()

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
