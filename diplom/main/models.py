from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User
#Модель Пользователи
from djangoProject import settings


class CustomUser(AbstractUser):
    account_type = models.CharField(max_length=100, verbose_name='Тип аккаунта')

    def __str__(self):
        return self.username

    class Meta:
        unique_together = ('username',)

# Модель магазина
class Shop(models.Model):
    username = models.CharField(max_length=256)
    name = models.CharField(max_length=256)
    accepting_orders = models.BooleanField(default=True)  # Новое поле

    def __str__(self):
        return self.name


# Модель категории
class Category(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    category_id = models.CharField(max_length=100)

    def __str__(self):
        return self.name


# Модель товаров
class Good(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='goods', null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='goods', null=True, blank=True)
    model = models.CharField(max_length=100, null=True, blank=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_rrc = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    quantity = models.IntegerField(null=True, blank=True)
    parameters = models.TextField(null=True, blank=True)
    characteristics = models.JSONField(null=True, blank=True)

    def __str__(self):
        return self.name


# Модель Корзина
class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)  # Связь с моделью Category
    model_name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=100)
    username = models.TextField()
    supplier_name = models.TextField()
    Address_street = models.TextField()

    def __str__(self):
        return self.category.name + " " + self.model_name
