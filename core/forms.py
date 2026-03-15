from django import forms
from .models import User

# ==========================================
# 1. ADMIN REGISTRATION FORM
# ==========================================
class InstructorRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'mt-1 block w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm',
        'placeholder': 'Temporary Password'
    }))

    class Meta:
        model = User
        fields = ['id_number', 'first_name', 'last_name', 'email', 'department']
        widgets = {
            'id_number': forms.TextInput(attrs={'class': 'mt-1 block w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm'}),
            'first_name': forms.TextInput(attrs={'class': 'mt-1 block w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm'}),
            'last_name': forms.TextInput(attrs={'class': 'mt-1 block w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm'}),
            'email': forms.EmailInput(attrs={'class': 'mt-1 block w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm'}),
            'department': forms.TextInput(attrs={'class': 'mt-1 block w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm'}),
        }

# ==========================================
# 2. INSTRUCTOR PROFILE SETTINGS FORM
# ==========================================
class InstructorProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'profile_picture']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'mt-1 block w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm'}),
            'last_name': forms.TextInput(attrs={'class': 'mt-1 block w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm'}),
            'email': forms.EmailInput(attrs={'class': 'mt-1 block w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm'}),
            'profile_picture': forms.FileInput(attrs={'class': 'mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100'})
        }
        
        