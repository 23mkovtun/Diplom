from django.contrib.auth.views import LogoutView
from django.urls import path, include
from . import views
from .views import send_invoice_to_supplier, supplier_orders_view, update_order_status
from allauth.socialaccount.views import SignupView

urlpatterns = [
    path('accounts/social/signup/google/', SignupView.as_view(), name='social_account_signup'),
    path('accounts/', include('allauth.urls')),
    path('', views.index_view, name='Home'),
    path('register/', views.register, name='register'),
    path('api/v1/drf-auth/', include('rest_framework.urls')),
    path('accounts/profile/', views.personal_account, name='personal-account'),
    path('logout/', views.logout_view, name='logout'),
    path('import_yaml/', views.import_yaml, name='import-yaml'),
    path('add_to_cart/<int:good_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove_from_cart/<int:cart_item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('api/v1/drf-auth/logout/', LogoutView.as_view(), name='api-logout'),
    path('send-invoice/', send_invoice_to_supplier, name='send_invoice_to_supplier'),
    path('supplier/orders/', supplier_orders_view, name='supplier_orders'),
    path('update_order_status/', update_order_status, name='update_order_status'),
]
