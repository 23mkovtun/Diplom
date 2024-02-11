import ast
import json
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User
from djangoProject import settings

# Модель пользователи
class CustomUser(AbstractUser):
    account_type = models.CharField(max_length=100, verbose_name='Тип аккаунта')

    def __str__(self):
        return self.username

    class Meta:
        unique_together = ('username',)

#Модель товары
class Good(models.Model):
    shop = models.ForeignKey('Shop', on_delete=models.CASCADE, related_name='goods')
    category = models.ForeignKey('Category', on_delete=models.CASCADE, related_name='goods')
    model = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    price_rrc = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    parameters = models.TextField()  # Параметры теперь будут сохраняться как JSON-строка

    def __str__(self):
        return self.name

    def get_parameters_dict(self):
        try:
            return ast.literal_eval(self.parameters)
        except (ValueError, SyntaxError):
            return {}

    def set_parameters_dict(self, parameters):
        self.parameters = json.dumps(parameters)

#Модель магазин
class Shop(models.Model):
    username = models.CharField(max_length=256)
    name = models.CharField(max_length=256)
    accepting_orders = models.BooleanField(default=True)

    def __str__(self):
        return self.name

#Модель категории
class Category(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    category_id = models.CharField(max_length=100)

    def __str__(self):
        return self.name

#Модель корзина
class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    model_name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=100)
    username = models.TextField()
    buyer_name = models.TextField()
    Address_street = models.TextField()

    def __str__(self):
        return self.category.name + " " + self.model_name
