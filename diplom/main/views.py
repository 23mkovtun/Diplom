import ast
import yaml
from .tasks import send_invoice_to_supplier_task, update_order_status_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from rest_framework import status
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from .forms import RegisterUserForm
from .models import Good, Cart, Category, Shop, CustomUser
from .serializers import GoodSerializer, UserCartSerializer, SupplierCartSerializer
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Cart
from rest_framework.throttling import UserRateThrottle

class MyThrottle(UserRateThrottle):
    scope = 'my_throttle'
    rate = '5/day'  # Пять запросов в день

@api_view(['POST'])
@throttle_classes([MyThrottle])
def send_invoice_to_supplier(request):
    """
    Отправить счет поставщику.
    """
    if request.method == 'POST':
        user_id = request.user.id
        send_invoice_to_supplier_task.delay(user_id)
        return redirect('personal-account')
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

@csrf_exempt
@api_view(['POST'])
@throttle_classes([MyThrottle])
def update_order_status(request):
    """
    Обновить статус заказа.
    """
    if request.method == "POST":
        order_id = request.POST.get("order_id")
        next_status = request.POST.get("next_status")
        update_order_status_task.delay(order_id, next_status)
        return JsonResponse({"success": True})
    else:
        return JsonResponse({"success": False, "error": "Метод не разрешен"})

def register(request):
    """
    Регистрация нового пользователя.
    """
    if request.method == "POST":
        form = RegisterUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])  # Хеширование пароля
            user.save()
            return redirect('Home')  # Перенаправление на главную страницу после успешной регистрации
    else:
        form = RegisterUserForm()
    return render(request, 'register.html', {'form': form})

@api_view(['GET'])
def index_view(request):
    """
    Отображение главной страницы.
    """
    current_user = request.user
    if current_user.is_authenticated:
        account_type = current_user.account_type
    else:
        account_type = None
    goods = Good.objects.all()
    for product in goods:
        product.formatted_parameters = format_parameters_for_template(product.parameters)
    context = {'account_type': account_type, 'goods': goods}
    return render(request, 'base.html', context)

@login_required
def personal_account(request):
    """
    Персональный кабинет пользователя.
    """
    current_user = request.user
    account_type = current_user.account_type
    user_products = Good.objects.filter(shop__username=current_user.username)
    for product in user_products:
        product.formatted_parameters = format_parameters_for_template(product.parameters)
    user_cart = Cart.objects.filter(user=current_user)

    # Получаем заказы поставщика
    supplier_orders = Cart.objects.filter(username=current_user.username)

    context = {
        'account_type': account_type,
        'user_products': user_products,
        'user_cart': user_cart,
        'supplier_orders': supplier_orders,  # Добавляем заказы поставщика в контекст
    }
    return render(request, 'personal_account.html', context)

def supplier_orders_view(request):
    """
    Отображение заказов поставщика.
    """
    if request.user.is_authenticated and request.user.account_type == 'Поставщик':
        supplier_orders = Cart.objects.filter(username=request.user.username)
        context = {'supplier_orders': supplier_orders}
        return render(request, 'supplier_orders.html', context)
    else:
        return redirect('login')  # Или другой URL для авторизации

@api_view(['POST', 'GET'])
@throttle_classes([MyThrottle])
def import_yaml(request):
    """
    Импорт данных из YAML-файла.
    """
    if request.method == 'POST' and request.FILES.get('yaml_file'):
        yaml_file = request.FILES['yaml_file']
        yaml_data = yaml.safe_load(yaml_file)
        shop_username = request.user.username
        shop_name = yaml_data.get('shop')
        shop, created = Shop.objects.get_or_create(username=shop_username, name=shop_name)
        categories_data = yaml_data.get('categories', [])
        for category_data in categories_data:
            category_id = category_data.get('id')
            category_name = category_data.get('name')
            category, created = Category.objects.get_or_create(shop=shop, category_id=category_id, defaults={'name': category_name})
        goods_data = yaml_data.get('goods', [])
        for good_data in goods_data:
            category_id = good_data['category']
            category = Category.objects.get(shop=shop, category_id=category_id)
            Good.objects.create(
                shop=shop,
                category=category,
                model=good_data['model'],
                name=good_data['name'],
                price=good_data['price'],
                price_rrc=good_data['price_rrc'],  # Убедитесь, что price_rrc устанавливается правильно
                quantity=good_data['quantity'],
                parameters=good_data['parameters']
            )
        return redirect('personal-account')
    elif request.method == 'GET':
        return render(request, 'import_yaml.html')

@api_view(['GET'])
def cart_list(request):
    """
    Получить список товаров в корзине пользователя.
    """
    carts = Cart.objects.filter(user=request.user)
    serializer = SupplierCartSerializer(carts, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@login_required
def add_to_cart(request, good_id):
    """
    Добавить товар в корзину пользователя.
    """
    if request.method == 'POST':
        try:
            good = Good.objects.get(id=good_id)
            # Получаем магазин, к которому принадлежит товар
            shop = good.shop
            supplier_username = shop.username  # Получаем логин поставщика

            # Проверяем, был ли передан адрес доставки в запросе
            delivery_address = request.data.get('delivery_address')

            # Создаем словарь с данными для сериализатора
            data = {
                'user': request.user.id,
                'category': good.category.id,
                'model_name': good.name,
                'price': good.price,
                'status': 'В корзине',
                'username': supplier_username,  # Сохраняем логин поставщика
                'supplier_name': request.user.username,
                'Address_street': delivery_address  # Добавляем адрес доставки в данные
            }

            # Создаем сериализатор с переданными данными
            serializer = UserCartSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                # После успешного добавления товара в корзину производим перенаправление на главную страницу
                return redirect('Home')
            # Если сериализатор не валиден, возвращаем ошибку
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Good.DoesNotExist:
            return Response({"error": "Товар не найден"}, status=status.HTTP_404_NOT_FOUND)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['POST'])
@login_required
def remove_from_cart(request, cart_item_id):
    """
    Удалить товар из корзины пользователя.
    """
    # Получаем текущего пользователя
    current_user = request.user
    # Получаем товар из корзины по его ID
    try:
        cart_item = Cart.objects.get(pk=cart_item_id, user=current_user)
    except Cart.DoesNotExist:
        # Если товар не найден в корзине пользователя, перенаправляем его обратно
        return redirect('personal-account')

    # Удаляем товар из корзины
    cart_item.delete()

    # Перенаправляем пользователя обратно в личный кабинет
    return redirect('personal-account')

def format_parameters_for_template(parameters):
    """
    Форматирование параметров товара для шаблона.
    """
    formatted_parameters = ""
    try:
        parameters_dict = ast.literal_eval(parameters)
        for key, value in parameters_dict.items():
            formatted_parameters += f"<p>{key}: {value}</p>"
    except (ValueError, SyntaxError):
        formatted_parameters = parameters
    return formatted_parameters

@api_view(['GET'])
def good_list(request):
    """
    Получить список всех товаров.
    """
    goods = Good.objects.all()
    serializer = GoodSerializer(goods, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def logout_view(request):
    """
    Выход пользователя из системы.
    """
    logout(request)
    return redirect('Home')
