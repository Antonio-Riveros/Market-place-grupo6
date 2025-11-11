from django.urls import path
from . import views

app_name = "market"

urlpatterns = [
    path("", views.product_list, name="productlist"),
    path("create/", views.product_create, name="productcreate"),
    path("edit/<int:pk>/", views.product_edit, name="product-edit"),
    path("delete/<int:pk>/", views.product_delete, name="product-delete"),

    # Carrito
    path("cart/", views.view_cart, name="view-cart"),
    path("add/<int:product_id>/", views.add_to_cart, name="add-to-cart"),
    path("cart/increase/<int:product_id>/", views.cart_increase, name="cart-increase"),
    path("cart/decrease/<int:product_id>/", views.cart_decrease, name="cart-decrease"),
    path("cart/remove/<int:product_id>/", views.cart_remove, name="cart-remove"),
    path("cart/summary/", views.cart_summary, name="cart-summary"),
    path("cart/data/", views.cart_data, name="cart-data"),
path('cart/generate-budget/', views.generate_budget, name='generate-budget'),
    # Mercado Pago
    path('crear-preferencia-carrito/', views.create_preference_cart, name='crear-preferencia-carrito'),

]

