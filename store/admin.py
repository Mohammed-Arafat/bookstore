
from django.contrib import admin

from .models import (
    Category,
    Author,
    Publisher,
    Book,
    CustomerProfile,
    Cart,
    CartItem,
    Order,
    OrderItem,
    Review,
)


# --------------------------------------------------
# CATEGORY
# --------------------------------------------------

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    ordering = ('name',)
    prepopulated_fields = {'slug': ('name',)}


# --------------------------------------------------
# AUTHOR
# --------------------------------------------------

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('name', 'email')
    search_fields = ('name', 'email')
    ordering = ('name',)


# --------------------------------------------------
# PUBLISHER
# --------------------------------------------------

@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ('name', 'website')
    search_fields = ('name',)
    ordering = ('name',)


# --------------------------------------------------
# BOOK
# --------------------------------------------------

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'isbn',
        'publisher',
        'price',
        'stock_quantity',
        'created_at',
    )

    list_filter = (
        'publisher',
        'categories',
        'created_at',
    )

    search_fields = (
        'title',
        'isbn',
        'authors__name',
        'categories__name',
        'publisher__name',
    )

    ordering = ('title',)

    readonly_fields = (
        'created_at',
        'updated_at',
    )

    filter_horizontal = (
        'authors',
        'categories',
    )

    list_select_related = ('publisher',)
    list_per_page = 20


# --------------------------------------------------
# CUSTOMER PROFILE
# --------------------------------------------------

@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'phone',
        'city',
        'postal_code',
    )

    search_fields = (
        'user__username',
        'user__email',
        'phone',
        'city',
    )

    list_filter = ('city',)
    ordering = ('user__username',)


# --------------------------------------------------
# CART ITEM INLINE
# --------------------------------------------------

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = ('book', 'quantity', 'subtotal')
    readonly_fields = ('subtotal',)


# --------------------------------------------------
# CART
# --------------------------------------------------

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'created_at',
        'updated_at',
        'total_price',
    )

    search_fields = (
        'user__username',
        'user__email',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
        'total_price',
    )

    ordering = ('-created_at',)
    inlines = (CartItemInline,)


# --------------------------------------------------
# CART ITEM
# --------------------------------------------------

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = (
        'cart',
        'book',
        'quantity',
        'subtotal',
    )

    search_fields = (
        'cart__user__username',
        'book__title',
    )

    list_filter = ('book__categories',)
    readonly_fields = ('subtotal',)


# --------------------------------------------------
# ORDER ITEM INLINE
# --------------------------------------------------

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = (
        'book',
        'quantity',
        'unit_price',
        'subtotal',
    )
    readonly_fields = ('subtotal',)


# --------------------------------------------------
# ORDER
# --------------------------------------------------

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number',
        'user',
        'status',
        'total_amount',
        'created_at',
    )

    list_filter = (
        'status',
        'created_at',
    )

    search_fields = (
        'order_number',
        'user__username',
        'user__email',
    )

    ordering = ('-created_at',)

    readonly_fields = (
        'order_number',
        'created_at',
        'updated_at',
        'total_amount',
    )

    inlines = (OrderItemInline,)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.total_amount = 0
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)

        order = form.instance

        # Recalculate the order total from its items
        order.total_amount = sum(
            item.subtotal
            for item in OrderItem.objects.filter(order=order)
        )

        order.save(update_fields=['total_amount'])


# --------------------------------------------------
# ORDER ITEM
# --------------------------------------------------

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        'order',
        'book',
        'quantity',
        'unit_price',
        'subtotal',
    )

    search_fields = (
        'order__order_number',
        'book__title',
    )

    readonly_fields = ('subtotal',)


# --------------------------------------------------
# REVIEW
# --------------------------------------------------

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        'book',
        'user',
        'rating',
        'created_at',
    )

    list_filter = (
        'rating',
        'created_at',
    )

    search_fields = (
        'book__title',
        'user__username',
        'comment',
    )

    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
