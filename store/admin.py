"""Admin so staff can manage catalog and orders out of the box."""
from django.contrib import admin
from django.utils.html import format_html

from .models import Cart, CartItem, Category, Order, OrderItem, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "price", "stock", "is_active", "thumbnail"]
    list_filter = ["is_active", "category", "created_at"]
    list_editable = ["price", "stock", "is_active"]
    search_fields = ["name", "description"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["created_at", "updated_at", "thumbnail"]
    list_per_page = 25

    @admin.display(description="Image")
    def thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:42px;border-radius:6px;" />', obj.image.url)
        return "—"


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["product", "product_name", "price", "quantity", "subtotal"]
    can_delete = False

    @admin.display(description="Subtotal")
    def subtotal(self, obj):
        return obj.subtotal


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["order_number", "full_name", "email", "status", "total_amount", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["order_number", "full_name", "email"]
    readonly_fields = ["order_number", "total_amount", "created_at", "updated_at"]
    inlines = [OrderItemInline]
    list_per_page = 25
    date_hierarchy = "created_at"


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ["product", "quantity", "subtotal"]

    @admin.display(description="Subtotal")
    def subtotal(self, obj):
        return obj.subtotal


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ["__str__", "item_count", "total", "updated_at"]
    inlines = [CartItemInline]
    readonly_fields = ["session_key", "created_at", "updated_at"]
