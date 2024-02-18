from __future__ import absolute_import, unicode_literals
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import Cart, CustomUser
from django.test import TestCase, Client
from django.urls import reverse
from .models import Good, Cart, Category, Shop, CustomUser
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
import json

@shared_task
def send_invoice_to_supplier_task(user_id):
    user = CustomUser.objects.get(id=user_id)
    supplier_usernames = Cart.objects.filter(user=user, status='В корзине').values_list('username', flat=True).distinct()

    for supplier_username in supplier_usernames:
        cart_items = Cart.objects.filter(user=user, status='В корзине', username=supplier_username)
        message = render_to_string('invoice_email.html', {'cart_items': cart_items})
        plain_message = strip_tags(message)
        supplier_email = CustomUser.objects.get(username=supplier_username, account_type='Поставщик').email

        send_mail(
            'Новый заказ от покупателя',
            plain_message,
            'from@example.com',
            [supplier_email],
            html_message=message,
        )

        cart_items.update(status='Заказ в обработке')

@shared_task
def update_order_status_task(order_id, next_status):
    cart = Cart.objects.get(pk=order_id)
    if cart.status == "Заказ в обработке" or cart.status == "Заказ отправлен":
        cart.status = next_status
        cart.save()
        user = CustomUser.objects.get(username=cart.supplier_name)
        buyer_email = user.email
        subject = "Изменение статуса заказа"
        message = f"Статус вашего заказа #{cart.id} был изменен на {next_status}\n"
        message += f"Заказ на адрес {cart.Address_street}\n"
        message += f"Название товара: {cart.model_name}\n"
        message += f"Цена: {cart.price}\n"
        send_mail(subject, message, None, [buyer_email])

class ViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(username='test_user', email='test@test.com', password='testpassword')
        self.shop = Shop.objects.create(username='test_shop', name='Test Shop')
        self.category = Category.objects.create(shop=self.shop, category_id='test_cat', name='Test Category')
        self.good = Good.objects.create(shop=self.shop, category=self.category, model='Test Model', name='Test Good', price=100, price_rrc=120, quantity=10, parameters='{"color": "red", "size": "M"}')
        self.cart = Cart.objects.create(user=self.user, category=self.category, model_name='Test Good', price=100, status='В корзине', username='test_shop', supplier_name='test_user')

    def test_send_invoice_to_supplier(self):
        # Авторизуем пользователя
        self.client.force_login(self.user)
        response = self.client.post(reverse('send-invoice-to-supplier'))
        self.assertEqual(response.status_code, 302)  # Проверяем, что запрос перенаправляет на главную страницу

    def test_update_order_status(self):
        response = self.client.post(reverse('update-order-status'), {'order_id': self.cart.id, 'next_status': 'new_status'})
        self.assertEqual(response.status_code, 200)  # Проверяем успешный ответ

    def test_register_view(self):
        response = self.client.post(reverse('register'), {'username': 'new_user', 'email': 'new_user@test.com', 'password': 'new_password'})
        self.assertEqual(response.status_code, 302)  # Проверяем, что запрос перенаправляет на главную страницу

    def test_index_view(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)  # Проверяем успешный ответ

    def test_personal_account_view(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('personal-account'))
        self.assertEqual(response.status_code, 200)  # Проверяем успешный ответ

    def test_supplier_orders_view(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('supplier-orders'))
        self.assertEqual(response.status_code, 302)  # Проверяем, что запрос перенаправляет на страницу авторизации

    def test_import_yaml_view(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('import-yaml'))
        self.assertEqual(response.status_code, 200)  # Проверяем успешный ответ

    def test_cart_list_view(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('cart-list'))
        self.assertEqual(response.status_code, 200)  # Проверяем успешный ответ

    def test_add_to_cart_view(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('add-to-cart', args=[self.good.id]), data=json.dumps({'delivery_address': 'Test Address'}), content_type='application/json')
        self.assertEqual(response.status_code, 302)  # Проверяем, что запрос перенаправляет на главную страницу

    def test_remove_from_cart_view(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('remove-from-cart', args=[self.cart.id]))
        self.assertEqual(response.status_code, 302)  # Проверяем, что запрос перенаправляет на страницу личного кабинета

    def test_good_list_view(self):
        response = self.client.get(reverse('good-list'))
        self.assertEqual(response.status_code, 200)  # Проверяем успешный ответ

    def test_logout_view(self):
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)  # Проверяем, что запрос перенаправляет на главную страницу