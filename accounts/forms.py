from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignUpForm(UserCreationForm):
    email=forms.CharField(max_length=254, required=True, widget=forms.EmailInput())
    first_name=forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'placeholder':'First Name'}))
    last_name=forms.CharField(max_length=100,required=True,widget=forms.TextInput(attrs={'placeholder':'Last name'}))
    class Meta:
        model=User 
        fields=('username','first_name','last_name','email','password1','password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user