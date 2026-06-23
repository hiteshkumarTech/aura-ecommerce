from django.urls import path

from . import views

app_name = "store"

urlpatterns = [
    path("", views.product_list, name="product_list"),
    path("search/", views.product_list, name="search"),
    path("category/<slug:category_slug>/", views.product_list, name="product_list_by_category"),
    path("product/<slug:slug>/", views.product_detail, name="product_detail"),
    # Cart
    path("cart/", views.cart_detail, name="cart_detail"),
    path("cart/add/<int:product_id>/", views.cart_add, name="cart_add"),
    path("cart/update/<int:product_id>/", views.cart_update, name="cart_update"),
    path("cart/remove/<int:product_id>/", views.cart_remove, name="cart_remove"),
    # Checkout & orders
    path("checkout/", views.checkout, name="checkout"),
    path("order/<str:order_number>/", views.order_confirmation, name="order_confirmation"),
    path("orders/", views.order_history, name="order_history"),
]
