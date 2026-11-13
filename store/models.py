
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
    RegexValidator,
)
from django.utils import timezone
import uuid


# ==========================================
# 1. CATEGORY MODEL
# ==========================================

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    slug = models.SlugField(max_length=120, unique=True)

    def __str__(self):
        return self.name


# ==========================================
# 2. AUTHOR MODEL
# ==========================================

class Author(models.Model):
    name = models.CharField(max_length=150)
    biography = models.TextField(blank=True)
    email = models.EmailField(blank=True)

    def __str__(self):
        return self.name


# ==========================================
# 3. PUBLISHER MODEL
# ==========================================

class Publisher(models.Model):
    name = models.CharField(max_length=150, unique=True)
    address = models.TextField(blank=True)
    website = models.URLField(blank=True)

    def __str__(self):
        return self.name


# ==========================================
# 4. BOOK MODEL
# ==========================================

class Book(models.Model):

    isbn = models.CharField(
        max_length=13,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^(?:\d{10}|\d{13})$',
                message="ISBN must contain 10 or 13 digits."
            )
        ]
    )

    title = models.CharField(max_length=200)

    description = models.TextField(blank=True)

    authors = models.ManyToManyField(
        Author,
        related_name='books'
    )

    categories = models.ManyToManyField(
        Category,
        related_name='books'
    )

    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.PROTECT,
        related_name='books'
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )

    stock_quantity = models.PositiveIntegerField(default=0)

    publication_date = models.DateField(null=True, blank=True)

    cover_image = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()

        if self.price is not None and self.price <= 0:
            raise ValidationError({
                'price': 'Book price must be greater than zero.'
            })

        if self.stock_quantity is not None and self.stock_quantity < 0:
            raise ValidationError({
                'stock_quantity': 'Stock cannot be negative.'
            })

    def __str__(self):
        return self.title


# ==========================================
# 5. CUSTOMER PROFILE MODEL
# ==========================================

class CustomerProfile(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    phone = models.CharField(max_length=20, blank=True)

    address = models.TextField(blank=True)

    city = models.CharField(max_length=100, blank=True)

    postal_code = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


# ==========================================
# 6. CART MODEL
# ==========================================

class Cart(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Cart"

    @property
    def total_price(self):
        return sum(item.subtotal for item in self.items.all())


# ==========================================
# 7. CART ITEM MODEL
# ==========================================

class CartItem(models.Model):

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )

    book = models.ForeignKey(
        Book,
        on_delete=models.PROTECT,
        related_name='cart_items'
    )

    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['cart', 'book'],
                name='unique_book_per_cart'
            )
        ]

    def clean(self):
        super().clean()

        if self.book_id and self.quantity:
            if self.quantity > self.book.stock_quantity:
                raise ValidationError({
                    'quantity': 'Requested quantity exceeds available stock.'
                })

    @property
    def subtotal(self):
        return self.book.price * self.quantity

    def __str__(self):
        return f"{self.book.title} x {self.quantity}"


# ==========================================
# 8. ORDER MODEL
# ==========================================

class Order(models.Model):

    class OrderStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        PROCESSING = 'PROCESSING', 'Processing'
        SHIPPED = 'SHIPPED', 'Shipped'
        DELIVERED = 'DELIVERED', 'Delivered'
        CANCELLED = 'CANCELLED', 'Cancelled'

    order_number = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='orders'
    )

    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING
    )

    shipping_address = models.TextField()

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()

        if self.total_amount is not None and self.total_amount < 0:
            raise ValidationError({
                'total_amount': 'Order total cannot be negative.'
            })

    def __str__(self):
        return str(self.order_number)


# ==========================================
# 9. ORDER ITEM MODEL
# ==========================================

class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )

    book = models.ForeignKey(
        Book,
        on_delete=models.PROTECT,
        related_name='order_items'
    )

    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )

    @property
    def subtotal(self):
        return self.unit_price * self.quantity

    def clean(self):
        super().clean()

        if self.quantity is not None and self.quantity < 1:
            raise ValidationError({
                'quantity': 'Order quantity must be at least 1.'
            })

    def __str__(self):
        return f"{self.book.title} - Order {self.order_id}"


# ==========================================
# 10. REVIEW MODEL
# ==========================================

class Review(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews'
    )

    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='reviews'
    )

    rating = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ]
    )

    comment = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'book'],
                name='unique_review_per_user_book'
            )
        ]

    def clean(self):
        super().clean()

        if self.rating is not None and not 1 <= self.rating <= 5:
            raise ValidationError({
                'rating': 'Rating must be between 1 and 5.'
            })

    def __str__(self):
        return f"{self.user.username} - {self.book.title}"
