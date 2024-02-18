from django import forms
from django.contrib.auth import get_user_model
from .models import Good

User = get_user_model()

class AddToCartForm(forms.Form):
    characteristics = forms.JSONField(required=False)  # Добавьте это поле

class RegisterUserForm(forms.ModelForm):
    username = forms.CharField(label="Логин")
    email = forms.EmailField(label="E-mail")
    first_name = forms.CharField(label="Имя")
    last_name = forms.CharField(label="Фамилия")
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput())
    password2 = forms.CharField(label="Повтор пароля", widget=forms.PasswordInput())
    account_type = forms.CharField(label="Тип аккаунта")

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password2', 'account_type']

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError("Пароли не совпадают")
        return cd['password']

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Такой E-mail уже есть")
        return email
