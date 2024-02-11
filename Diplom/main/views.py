import ast
import yaml
from datetime import datetime
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .forms import RegisterUserForm
from .models import Good, Cart, Category, Shop, CustomUser
from .serializers import GoodSerializer, UserCartSerializer, SupplierCartSerializer, PasswordResetSerializer
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Cart
from rest_framework.views import APIView
from django.http import HttpResponse


def add_parameter(request):
    if request.method == 'POST':
        product_id = request.POST.get('product')
        param_name = request.POST.get('param_name')
        param_value = request.POST.get('param_value')

        product = Good.objects.get(pk=product_id)

        parameters = product.get_parameters_dict()
        parameters[param_name] = param_value

        product.set_parameters_dict(parameters)
        product.save()

        return redirect('personal-account')
    else:
        current_user = request.user
        user_products = Good.objects.filter(shop__username=current_user.username)
        return render(request, 'add_parameter.html', {'user_products': user_products})

def export_goods_to_yaml(request):
    if request.method == 'POST':
        current_user = request.user

        shop = Shop.objects.get(username=current_user.username)

        goods = Good.objects.filter(shop=shop)

        data = {
            'shop': shop.name,
            'categories': [],
            'goods': []
        }

        categories = Category.objects.filter(shop=shop)
        for category in categories:
            data['categories'].append({'id': str(category.category_id), 'name': category.name})

        for good in goods:
            good_data = {
                'id': str(good.id),
                'category': str(good.category.category_id),
                'model': good.model,
                'name': good.name,
                'price': float(good.price),
                'price_rrc': float(good.price_rrc),
                'quantity': good.quantity,
                'parameters': yaml.safe_load(good.parameters),
            }
            data['goods'].append(good_data)

        yaml_data = yaml.dump(data, allow_unicode=True)

        response = HttpResponse(yaml_data, content_type='text/yaml')
        response['Content-Disposition'] = f'attachment; filename="goods_{datetime.now().date()}.yaml"'
        return response
    else:
        return render(request, 'your_app/export_goods_to_yaml.html')

class PasswordResetAPIView(APIView):
    serializer_class = PasswordResetSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return redirect('Home')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
def update_order_status(request):
    if request.method == "POST":
        order_id = request.POST.get("order_id")
        next_status = request.POST.get("next_status")
        try:
            cart = Cart.objects.get(pk=order_id)

            if cart.status == "Заказ в обработке" or cart.status == "Заказ отправлен":
                cart.status = next_status
                cart.save()

                user = CustomUser.objects.get(username=cart.buyer_name)

                buyer_email = user.email
                subject = "Изменение статуса заказа"

                message = f"Статус вашего заказа #{cart.id} был изменен на {next_status}\n"
                message += f"Заказ на адрес {cart.Address_street}\n"
                message += f"Название товара: {cart.model_name}\n"
                message += f"Цена: {cart.price}\n"

                send_mail(subject, message, None, [buyer_email])

                return JsonResponse({"success": True})
            else:
                return JsonResponse({"success": False, "error": "Недопустимый статус для обновления"})
        except Cart.DoesNotExist:
            return JsonResponse({"success": False, "error": "Заказ не найден"})
        except CustomUser.DoesNotExist:
            return JsonResponse({"success": False, "error": "Пользователь не найден"})
    else:
        return JsonResponse({"success": False, "error": "Метод не разрешен"})

@api_view(['POST'])
def send_invoice_to_supplier(request):
    if request.method == 'POST':

        user = request.user

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

        return redirect('personal-account')
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

def register(request):
    if request.method == "POST":
        form = RegisterUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            return redirect('Home')
    else:
        form = RegisterUserForm()
    return render(request, 'register.html', {'form': form})

@api_view(['GET'])
def index_view(request):
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
    current_user = request.user
    account_type = current_user.account_type
    user_products = Good.objects.filter(shop__username=current_user.username)
    for product in user_products:
        product.formatted_parameters = format_parameters_for_template(product.parameters)
    user_cart = Cart.objects.filter(user=current_user)

    supplier_orders = Cart.objects.filter(username=current_user.username)

    context = {
        'account_type': account_type,
        'user_products': user_products,
        'user_cart': user_cart,
        'supplier_orders': supplier_orders,
    }
    return render(request, 'personal_account.html', context)

def supplier_orders_view(request):
    if request.user.is_authenticated and request.user.account_type == 'Поставщик':
        supplier_orders = Cart.objects.filter(username=request.user.username)
        context = {'supplier_orders': supplier_orders}
        return render(request, 'supplier_orders.html', context)
    else:
        return redirect('login')

@api_view(['POST', 'GET'])
def import_yaml(request):
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
                price_rrc=good_data['price_rrc'],
                quantity=good_data['quantity'],
                parameters=good_data['parameters']
            )
        return redirect('personal-account')
    elif request.method == 'GET':
        return render(request, 'import_yaml.html')

@api_view(['GET'])
def cart_list(request):
    carts = Cart.objects.filter(user=request.user)
    serializer = SupplierCartSerializer(carts, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@login_required
def add_to_cart(request, good_id):
    if request.method == 'POST':
        try:
            good = Good.objects.get(id=good_id)
            shop = good.shop
            supplier_username = shop.username
            delivery_address = request.data.get('delivery_address')
            data = {
                'user': request.user.id,
                'category': good.category.id,
                'model_name': good.name,
                'price': good.price,
                'status': 'В корзине',
                'username': supplier_username,
                'buyer_name': request.user.username,
                'Address_street': delivery_address
            }
            serializer = UserCartSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return redirect('Home')
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Good.DoesNotExist:
            return Response({"error": "Товар не найден"}, status=status.HTTP_404_NOT_FOUND)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['POST'])
@login_required
def remove_from_cart(request, cart_item_id):
    current_user = request.user
    try:
        cart_item = Cart.objects.get(pk=cart_item_id, user=current_user)
    except Cart.DoesNotExist:
        return redirect('personal-account')
    cart_item.delete()
    return redirect('personal-account')

def format_parameters_for_template(parameters):
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
    goods = Good.objects.all()
    serializer = GoodSerializer(goods, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def logout_view(request):
    logout(request)
    return redirect('Home')