from django import forms
from .models import Pengguna
from django.core.exceptions import ValidationError

class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a password',
            'id': 'password'
        }),
        label='Password',
        min_length=8,
        help_text='Password must be at least 8 characters long.'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password',
            'id': 'confirm_password'
        }),
        label='Confirm Password',
        min_length=8
    )
    
    class Meta:
        model = Pengguna
        fields = ['nama_user', 'email_user']
        widgets = {
            'nama_user': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'John Doe',
                'id': 'nama_user'
            }),
            'email_user': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'name@example.com',
                'id': 'email_user'
            }),
        }
        labels = {
            'nama_user': 'Full Name',
            'email_user': 'Email'
        }
    
    def clean_email_user(self):
        email = self.cleaned_data.get('email_user')
        if Pengguna.objects.filter(email_user=email).exists():
            raise ValidationError('Email has already been registered. Please use a different email.')
        return email
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password and len(password) < 8:
            raise ValidationError('Password must be at least 8 characters long.')
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password:
            if password != confirm_password:
                raise ValidationError({
                    'confirm_password': 'Passwords do not match.'
                })
        
        return cleaned_data
    
    def save(self, commit=True):
        pengguna = super().save(commit=False)
        
        try:
            # Generate ID user otomatis
            last_user = Pengguna.objects.order_by('-id_user').first()
            if last_user and last_user.id_user.startswith('U'):
                last_number = int(last_user.id_user[1:])
                new_id = f"U{str(last_number + 1).zfill(4)}"
            else:
                new_id = "U0001"
            
            pengguna.id_user = new_id
            pengguna.set_password(self.cleaned_data['password'])
            
            if commit:
                pengguna.save()
                print(f"✅ User berhasil dibuat: {pengguna.id_user} - {pengguna.email_user}")
            
            return pengguna
        except Exception as e:
            print(f"❌ Error saat save: {e}")
            raise