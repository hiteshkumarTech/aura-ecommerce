"""Expose a lightweight cart summary to every template (navbar badge)."""
from decimal import Decimal

from .models import Cart


def cart_summary(request):
    count, total = 0, Decimal("0.00")
    cart = None

    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
    elif request.session.session_key:
        cart = Cart.objects.filter(
            session_key=request.session.session_key, user__isnull=True
        ).first()

    if cart:
        # Prefetched once; cheap for typical cart sizes.
        items = list(cart.items.select_related("product"))
        count = sum(i.quantity for i in items)
        total = sum((i.subtotal for i in items), Decimal("0.00"))

    return {"cart_count": count, "cart_total": total}
