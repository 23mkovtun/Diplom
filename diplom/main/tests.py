from django.test import TestCase, Client
from django.urls import reverse
from .models import Good, CustomUser


class YourAppNameTestCase(TestCase):
    def setUp(self):
        # Создаем тестового пользователя
        self.user = CustomUser.objects.create_user(username='user3', password='123')

        # Создаем несколько тестовых товаров
        Good.objects.create(name='Test Good 1', price=10)
        Good.objects.create(name='Test Good 2', price=20)

        # Создаем клиента для отправки тестовых запросов
        self.client = Client()

    def test_index_view(self):
        # Проверяем, что страница index возвращает код состояния 200
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)

        # Проверяем, что на странице index есть как минимум два товара
        self.assertQuerysetEqual(response.context['goods'], ['<Good: Test Good 1>', '<Good: Test Good 2>'])

    def test_login_required_for_personal_account(self):
        # Проверяем, что страница personal_account требует аутентификации пользователя
        response = self.client.get(reverse('personal-account'))
        self.assertEqual(response.status_code, 302)  # Ожидаем редирект на страницу входа

    # Добавьте здесь другие тесты для ваших представлений
