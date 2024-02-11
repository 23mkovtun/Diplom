from rest_framework import serializers
from .models import Good, Cart, Shop, Category, CustomUser
from django.contrib.auth.forms import PasswordResetForm
from django.shortcuts import redirect
from django.views.generic.base import TemplateView


class GoodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Good
        fields = '__all__'

class UserCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ['user', 'category', 'model_name', 'price', 'status', 'username', 'buyer_name', 'Address_street']

class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ['id', 'username', 'name', 'accepting_orders']

class SupplierCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = '__all__'

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Пользователь с указанным email не найден.")
        return value

    def save(self):
        form = PasswordResetForm(data=self.validated_data)
        if form.is_valid():
            request = self.context.get('request')
            form.save(request=request)

class CustomPasswordResetCompleteView(TemplateView):
    template_name = 'password_reset_complete.html'
    def get(self, request, *args, **kwargs):
        return redirect('Home')


