from django import forms
from django.contrib.auth.models import User
from .models import StudentProfile

class StudentSignupForm(forms.ModelForm):
    # Standard User Fields
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    
    # Extra Profile Fields from your StudentProfile model
    phone = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}))
    college = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'College Name'}))
    course = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Course Name'}))
    location = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Location'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            # This line automatically creates the Profile when you sign up
            StudentProfile.objects.create(
                user=user,
                phone=self.cleaned_data['phone'],
                college=self.cleaned_data['college'],
                course=self.cleaned_data['course'],
                location=self.cleaned_data['location']
            )
        return user