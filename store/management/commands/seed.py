"""
Populate the database with demo categories and products.

Generates clean placeholder images with Pillow so the storefront looks
populated without any external assets. Idempotent: safe to run repeatedly.

Usage:
    python manage.py seed
    python manage.py seed --flush   # wipe catalog first
"""
import hashlib
import io
from decimal import Decimal

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image, ImageDraw, ImageFont

from store.models import Category, Product

CATALOG = {
    "Audio": [
        ("Aer Wireless Headphones", "Over-ear ANC headphones with 40h battery life and USB-C fast charge.", "199.00", 25),
        ("Pebble Bluetooth Speaker", "Pocket-sized speaker with deep bass and IP67 water resistance.", "59.00", 60),
        ("Loop Earbuds Pro", "True-wireless earbuds with adaptive noise cancelling and wireless charging.", "129.00", 40),
    ],
    "Workspace": [
        ("Mono Mechanical Keyboard", "Hot-swappable 75% keyboard with PBT keycaps and gasket mount.", "149.00", 30),
        ("Glide Ergonomic Mouse", "Silent-click wireless mouse with 4000 DPI sensor and USB-C.", "49.00", 75),
        ("Arc Monitor Light Bar", "Asymmetric LED light bar that reduces glare with auto-dimming.", "69.00", 50),
        ("Riser Laptop Stand", "Aluminium stand with adjustable height and cable routing.", "39.00", 80),
    ],
    "Home": [
        ("Lumen Smart Bulb (4-pack)", "Tunable white and color bulbs with app and voice control.", "44.00", 100),
        ("Brew Pour-Over Kettle", "Gooseneck kettle with variable temperature and a 1L capacity.", "89.00", 35),
        ("Drift Aroma Diffuser", "Ultrasonic diffuser with ambient lighting and an 8h timer.", "34.00", 65),
    ],
    "Bags": [
        ("Transit Backpack 22L", "Weatherproof commuter backpack with a padded 16\" laptop sleeve.", "119.00", 45),
        ("Field Sling Bag", "Everyday crossbody sling with quick-access magnetic buckle.", "59.00", 55),
    ],
    "Wearables": [
        ("Pulse Smartwatch", "AMOLED fitness watch with GPS, SpO2, and a 14-day battery.", "179.00", 28),
        ("Track Fitness Band", "Lightweight band with heart-rate and sleep tracking.", "49.00", 90),
    ],
}

# Palette used to tint generated placeholder images (background, foreground).
PALETTE = [
    ((237, 233, 254), (76, 29, 149)),
    ((219, 234, 254), (30, 58, 138)),
    ((220, 252, 231), (6, 78, 59)),
    ((254, 226, 226), (127, 29, 29)),
    ((255, 237, 213), (124, 45, 18)),
    ((224, 242, 254), (12, 74, 110)),
    ((243, 232, 255), (88, 28, 135)),
]


def _font(size: int):
    """Best-effort TrueType font with a graceful fallback."""
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def make_placeholder(name: str) -> ContentFile:
    """Render a 800x800 placeholder image with the product initials."""
    digest = int(hashlib.md5(name.encode()).hexdigest(), 16)
    bg, fg = PALETTE[digest % len(PALETTE)]
    size = 800
    img = Image.new("RGB", (size, size), bg)
    draw = ImageDraw.Draw(img)

    initials = "".join(word[0] for word in name.split()[:2]).upper()
    font = _font(280)
    box = draw.textbbox((0, 0), initials, font=font)
    tw, th = box[2] - box[0], box[3] - box[1]
    draw.text(
        ((size - tw) / 2 - box[0], (size - th) / 2 - box[1]),
        initials, fill=fg, font=font,
    )
    # Subtle frame for a more "product card" feel.
    draw.rounded_rectangle([24, 24, size - 24, size - 24], radius=36, outline=fg, width=4)

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=85)
    return ContentFile(buffer.getvalue())


class Command(BaseCommand):
    help = "Seed the database with demo categories and products."

    def add_arguments(self, parser):
        parser.add_argument("--flush", action="store_true", help="Delete existing catalog first.")

    def handle(self, *args, **options):
        if options["flush"]:
            Product.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(self.style.WARNING("Cleared existing catalog."))

        created = 0
        for category_name, products in CATALOG.items():
            category, _ = Category.objects.get_or_create(name=category_name)
            for name, description, price, stock in products:
                if Product.objects.filter(name=name).exists():
                    continue
                product = Product(
                    category=category,
                    name=name,
                    description=description,
                    price=Decimal(price),
                    stock=stock,
                )
                product.image.save(f"{product.slug or name}.jpg", make_placeholder(name), save=False)
                product.save()
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Seed complete. {created} new product(s); "
            f"{Category.objects.count()} categories, {Product.objects.count()} products total."
        ))
