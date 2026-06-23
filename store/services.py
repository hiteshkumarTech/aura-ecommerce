"""
Business logic kept out of views: cart resolution, cart merging on login,
and transactional order placement with stock control.
"""
from __future__ import annotations

from django.db import transaction

from .models import Cart, CartItem, Order, OrderItem, Product


class InsufficientStock(Exception):
    """Raised when a requested quantity exceeds available stock."""

    def __init__(self, product: Product, available: int):
        self.product = product
        self.available = available
        super().__init__(f"Only {available} of '{product.name}' left in stock.")


def get_or_create_cart(request) -> Cart:
    """Return the cart for the current user or anonymous session."""
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart

    if not request.session.session_key:
        request.session.create()
    cart, _ = Cart.objects.get_or_create(
        session_key=request.session.session_key, user__isnull=True
    )
    return cart


def add_to_cart(cart: Cart, product: Product, quantity: int = 1) -> CartItem:
    """
    Add (or increment) a product in the cart, validated against stock.

    On failure the cart is left unchanged: a row created by get_or_create is
    rolled back so a rejected add never leaves a stray line behind.
    """
    item, created = CartItem.objects.get_or_create(
        cart=cart, product=product, defaults={"quantity": 0}
    )
    desired = item.quantity + quantity
    if desired > product.stock:
        if created:
            item.delete()
        raise InsufficientStock(product, product.stock)
    item.quantity = desired
    item.save()
    return item


def set_cart_quantity(cart: Cart, product: Product, quantity: int) -> CartItem | None:
    """Set an exact quantity; removing the line when quantity <= 0."""
    if quantity <= 0:
        CartItem.objects.filter(cart=cart, product=product).delete()
        return None
    if quantity > product.stock:
        raise InsufficientStock(product, product.stock)
    item, _ = CartItem.objects.get_or_create(cart=cart, product=product)
    item.quantity = quantity
    item.save()
    return item


def merge_session_cart(request, user, old_session_key: str | None) -> None:
    """
    Merge an anonymous session cart into the user's cart at login time.

    Must be called with the session key captured *before* login(), because
    Django cycles the session key during authentication.
    """
    if not old_session_key:
        return
    try:
        session_cart = Cart.objects.get(session_key=old_session_key, user__isnull=True)
    except Cart.DoesNotExist:
        return

    user_cart, _ = Cart.objects.get_or_create(user=user)
    for item in session_cart.items.select_related("product"):
        existing = user_cart.items.filter(product=item.product).first()
        if existing:
            # Combine quantities but never exceed stock.
            existing.quantity = min(existing.quantity + item.quantity, item.product.stock)
            existing.save()
        else:
            item.cart = user_cart
            item.save()
    session_cart.delete()


@transaction.atomic
def place_order(cart: Cart, *, shipping: dict, user=None) -> Order:
    """
    Convert a cart into an order atomically.

    Locks each product row (SELECT ... FOR UPDATE) to prevent overselling under
    concurrent checkouts, snapshots unit prices, decrements stock, then clears
    the cart. Any stock failure rolls the whole thing back.
    """
    items = list(cart.items.select_related("product"))
    if not items:
        raise ValueError("Cannot place an order with an empty cart.")

    order = Order.objects.create(user=user, **shipping)

    # Lock in a deterministic order (by pk) to avoid deadlocks.
    product_ids = sorted(item.product_id for item in items)
    locked = {
        p.pk: p
        for p in Product.objects.select_for_update().filter(pk__in=product_ids)
    }

    for item in items:
        product = locked[item.product_id]
        if item.quantity > product.stock:
            raise InsufficientStock(product, product.stock)
        product.stock -= item.quantity
        product.save(update_fields=["stock"])
        OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            price=product.price,
            quantity=item.quantity,
        )

    order.recalculate_total()
    order.status = Order.Status.PAID  # payment is simulated; see checkout view
    order.save(update_fields=["total_amount", "status"])

    cart.items.all().delete()
    return order
