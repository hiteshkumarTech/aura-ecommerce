"""Store views: catalog, cart, and checkout."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import CheckoutForm
from .models import Category, Order, Product
from .services import (
    InsufficientStock,
    add_to_cart,
    get_or_create_cart,
    place_order,
    set_cart_quantity,
)

PAGE_SIZE = 9


def product_list(request, category_slug=None):
    """Catalog with category filtering, keyword search, and pagination."""
    categories = Category.objects.all()
    products = Product.objects.filter(is_active=True).select_related("category")

    active_category = None
    if category_slug:
        active_category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=active_category)

    query = request.GET.get("q", "").strip()
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))

    paginator = Paginator(products, PAGE_SIZE)
    page = paginator.get_page(request.GET.get("page"))

    return render(request, "store/product_list.html", {
        "categories": categories,
        "active_category": active_category,
        "products": page.object_list,
        "page_obj": page,
        "query": query,
    })


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related("category"), slug=slug, is_active=True
    )
    related = (
        Product.objects.filter(category=product.category, is_active=True)
        .exclude(pk=product.pk)[:4]
    )
    return render(request, "store/product_detail.html", {
        "product": product,
        "related_products": related,
    })


@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    cart = get_or_create_cart(request)
    try:
        quantity = max(1, int(request.POST.get("quantity", 1)))
    except (TypeError, ValueError):
        quantity = 1
    try:
        add_to_cart(cart, product, quantity)
        messages.success(request, f"Added “{product.name}” to your cart.")
    except InsufficientStock as exc:
        messages.error(request, str(exc))

    # Return to the page the user came from, but only when it's a safe
    # same-site path — prevents open-redirects via a forged `next` value.
    next_url = request.POST.get("next", "")
    if not url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        next_url = reverse("store:cart_detail")
    return HttpResponseRedirect(next_url)


@require_POST
def cart_update(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    cart = get_or_create_cart(request)
    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = 1
    try:
        set_cart_quantity(cart, product, quantity)
    except InsufficientStock as exc:
        messages.error(request, str(exc))
    return redirect("store:cart_detail")


@require_POST
def cart_remove(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    cart = get_or_create_cart(request)
    set_cart_quantity(cart, product, 0)
    messages.info(request, f"Removed “{product.name}” from your cart.")
    return redirect("store:cart_detail")


def cart_detail(request):
    cart = get_or_create_cart(request)
    items = cart.items.select_related("product")
    return render(request, "store/cart.html", {"cart": cart, "items": items})


@login_required
def checkout(request):
    cart = get_or_create_cart(request)
    items = cart.items.select_related("product")

    if not items:
        messages.info(request, "Your cart is empty.")
        return redirect("store:product_list")

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                # NOTE: payment is simulated here. To accept real payments,
                # create a PaymentIntent (e.g. Stripe) before place_order and
                # only finalize on a confirmed charge / webhook.
                order = place_order(cart, shipping=form.cleaned_data, user=request.user)
            except InsufficientStock as exc:
                messages.error(request, f"{exc} Please adjust your cart.")
                return redirect("store:cart_detail")
            except ValueError:
                messages.info(request, "Your cart is empty.")
                return redirect("store:product_list")
            messages.success(request, "Payment received — your order is confirmed.")
            return redirect("store:order_confirmation", order_number=order.order_number)
    else:
        # Prefill contact details from the logged-in user where possible.
        initial = {"email": request.user.email, "full_name": request.user.get_full_name()}
        form = CheckoutForm(initial=initial)

    return render(request, "store/checkout.html", {"cart": cart, "items": items, "form": form})


@login_required
def order_confirmation(request, order_number):
    order = get_object_or_404(
        Order.objects.prefetch_related("items"), order_number=order_number, user=request.user
    )
    return render(request, "store/order_confirmation.html", {"order": order})


@login_required
def order_history(request):
    orders = (
        Order.objects.filter(user=request.user)
        .prefetch_related("items")
        .order_by("-created_at")
    )
    return render(request, "store/order_history.html", {"orders": orders})
