import os
from celery import Celery
# Устанавливаем переменную окружения DJANGO_SETTINGS_MODULE
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')

# Создаем экземпляр приложения Celery
app = Celery('djangoProject')

# Загружаем настройки из файла settings.py проекта Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Находим и регистрируем задачи из всех файлов tasks.py в приложениях Django
app.autodiscover_tasks()