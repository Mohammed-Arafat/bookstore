
from rest_framework import serializers
from django.contrib.auth import get_user_model

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
    Review
)

User = get_user_model()


# ==========================================
# 1. CATEGORY SERIALIZER
# ==========================================

class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = '__all__'

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                "Category name cannot be empty."
            )
        return value.strip()


# ==========================================
# 2. AUTHOR SERIALIZER
# ==========================================

class AuthorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Author
        fields = '__all__'

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                "Author name cannot be empty."
            )
        return value.strip()


# ==========================================
# 3. PUBLISHER SERIALIZER
# ==========================================

class PublisherSerializer(serializers.ModelSerializer):

    class Meta:
        model = Publisher
        fields = '__all__'

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                "Publisher name cannot be empty."
            )
        return value.strip()


# ==========================================
# 4. BOOK SERIALIZER
# ==========================================

class BookSerializer(serializers.ModelSerializer):

    # Nested read-only representations
    authors = AuthorSerializer(many=True, read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    publisher = PublisherSerializer(read_only=True)

    # Write-only relationship IDs
    author_ids = serializers.PrimaryKeyRelatedField(
        queryset=Author.objects.all(),
        many=True,
        source='authors',
        write_only=True
    )

    category_ids = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        many=True,
        source='categories',
        write_only=True
    )

    publisher_id = serializers.PrimaryKeyRelatedField(
        queryset=Publisher.objects.all(),
        source='publisher',
        write_only=True
    )

    class Meta:
        model = Book
        fields = [
            'id',
            'isbn',
            'title',
            'description',
            'authors',
            'author_ids',
            'categories',
            'category_ids',
            'publisher',
            'publisher_id',
            'price',
            'stock_quantity',
            'publication_date',
            'cover_image',
            'created_at',
            'updated_at'
        ]

        read_only_fields = [
            'id',
            'created_at',
            'updated_at'
        ]

    def validate_isbn(self, value):
        if not value.isdigit() or len(value) not in (10, 13):
            raise serializers.ValidationError(
                "ISBN must contain exactly 10 or 13 digits."
            )
        return value

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Book price must be greater than zero."
            )
        return value

    def validate_stock_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Stock quantity cannot be negative."
            )
        return value

    def validate(self, data):
        if self.instance is None:
            if not data.get('authors'):
                raise serializers.ValidationError({
                    'author_ids': 'At least one author is required.'
                })

            if not data.get('categories'):
                raise serializers.ValidationError({
                    'category_ids': 'At least one category is required.'
                })

        return data


# ==========================================
# 5. CUSTOMER PROFILE SERIALIZER
# ==========================================

class CustomerProfileSerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        source='user.username',
        read_only=True
    )

    class Meta:
        model = CustomerProfile
        fields = [
            'id',
            'user',
            'username',
            'phone',
            'address',
            'city',
            'postal_code'
        ]

        read_only_fields = ['id', 'user', 'username']


# ==========================================
# 6. CART SERIALIZER
# ==========================================

class CartSerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        source='user.username',
        read_only=True
    )

    items = serializers.SerializerMethodField()

    total_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = Cart
        fields = [
            'id',
            'user',
            'username',
            'items',
            'total_price',
            'created_at',
            'updated_at'
        ]

        read_only_fields = [
            'id',
            'user',
            'username',
            'created_at',
            'updated_at'
        ]

    def get_items(self, obj):
        return CartItemSerializer(
            obj.items.all(),
            many=True,
            context=self.context
        ).data


# ==========================================
# 7. CART ITEM SERIALIZER
# ==========================================

class CartItemSerializer(serializers.ModelSerializer):

    book_title = serializers.CharField(
        source='book.title',
        read_only=True
    )

    book_price = serializers.DecimalField(
        source='book.price',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    subtotal = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )

    book_id = serializers.PrimaryKeyRelatedField(
        queryset=Book.objects.all(),
        source='book'
    )

    class Meta:
        model = CartItem
        fields = [
            'id',
            'cart',
            'book_id',
            'book_title',
            'book_price',
            'quantity',
            'subtotal'
        ]

        read_only_fields = ['id', 'cart']

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError(
                "Quantity must be at least 1."
            )

        return value

    def validate(self, data):
        book = data.get('book', self.instance.book if self.instance else None)
        quantity = data.get(
            'quantity',
            self.instance.quantity if self.instance else 1
        )

        if book and quantity > book.stock_quantity:
            raise serializers.ValidationError({
                'quantity': 'Requested quantity exceeds available stock.'
            })

        return data


# ==========================================
# 8. ORDER SERIALIZER
# ==========================================

class OrderSerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        source='user.username',
        read_only=True
    )

    items = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id',
            'order_number',
            'user',
            'username',
            'status',
            'shipping_address',
            'total_amount',
            'items',
            'created_at',
            'updated_at'
        ]

        read_only_fields = [
            'id',
            'order_number',
            'user',
            'username',
            'status',
            'total_amount',
            'created_at',
            'updated_at'
        ]

    def get_items(self, obj):
        return OrderItemSerializer(
            obj.items.all(),
            many=True,
            context=self.context
        ).data

    def validate_shipping_address(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                "Shipping address cannot be empty."
            )
        return value.strip()


# ==========================================
# 9. ORDER ITEM SERIALIZER
# ==========================================

class OrderItemSerializer(serializers.ModelSerializer):

    book_title = serializers.CharField(
        source='book.title',
        read_only=True
    )

    subtotal = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )

    book_id = serializers.PrimaryKeyRelatedField(
        queryset=Book.objects.all(),
        source='book'
    )

    class Meta:
        model = OrderItem
        fields = [
            'id',
            'order',
            'book_id',
            'book_title',
            'quantity',
            'unit_price',
            'subtotal'
        ]

        read_only_fields = ['id', 'unit_price', 'subtotal']

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError(
                "Order quantity must be at least 1."
            )
        return value

    def validate(self, data):
        book = data.get('book', self.instance.book if self.instance else None)
        quantity = data.get(
            'quantity',
            self.instance.quantity if self.instance else 1
        )

        if book and quantity > book.stock_quantity:
            raise serializers.ValidationError({
                'quantity': 'Requested quantity exceeds available stock.'
            })

        return data


# ==========================================
# 10. REVIEW SERIALIZER
# ==========================================

class ReviewSerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        source='user.username',
        read_only=True
    )

    book_title = serializers.CharField(
        source='book.title',
        read_only=True
    )

    class Meta:
        model = Review
        fields = [
            'id',
            'user',
            'username',
            'book',
            'book_title',
            'rating',
            'comment',
            'created_at'
        ]

        read_only_fields = [
            'id',
            'user',
            'username',
            'book_title',
            'created_at'
        ]

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError(
                "Rating must be between 1 and 5."
            )
        return value

    def validate(self, data):
        book = data.get(
            'book',
            self.instance.book if self.instance else None
        )

        user = self.context['request'].user

        if book and user.is_authenticated:
            existing_review = Review.objects.filter(
                user=user,
                book=book
            )

            if self.instance:
                existing_review = existing_review.exclude(
                    pk=self.instance.pk
                )

            if existing_review.exists():
                raise serializers.ValidationError(
                    "You have already reviewed this book."
                )

        return data
