# serializers.py

from rest_framework import serializers
from .models import Good, Cart, Shop, Category

class GoodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Good
        fields = '__all__'

class UserCartSerializer(serializers.ModelSerializer):
    """
    Сериализатор для корзины пользователя.

    Fields:
    - user: поле, которое содержит информацию о пользователе.
    - category: поле, которое содержит информацию о категории товара в корзине.
    - model_name: поле, которое содержит название модели товара в корзине.
    - price: поле, которое содержит цену товара в корзине.
    - status: поле, которое содержит статус товара в корзине.
    - username: поле, которое содержит имя поставщика товара.
    - supplier_name: поле, которое содержит имя пользователя-поставщика.
    - Address_street: поле, которое содержит адрес доставки товара.
    """
    class Meta:
        model = Cart
        fields = ['user', 'category', 'model_name', 'price', 'status', 'username', 'supplier_name', 'Address_street']

class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ['id', 'username', 'name', 'accepting_orders']

class SupplierCartSerializer(serializers.ModelSerializer):
    """
    Сериализатор для корзины поставщика.

    Fields:
    - все: все поля из модели Cart.
    """
    class Meta:
        model = Cart
        fields = '__all__'
