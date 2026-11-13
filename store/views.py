
from decimal import Decimal

from django.db import transaction
from django.db.models import F
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
    IsAdminUser,
    BasePermission,
    SAFE_METHODS
)
from rest_framework.response import Response

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

from .serializers import (
    CategorySerializer,
    AuthorSerializer,
    PublisherSerializer,
    BookSerializer,
    CustomerProfileSerializer,
    CartSerializer,
    CartItemSerializer,
    OrderSerializer,
    OrderItemSerializer,
    ReviewSerializer
)


# ==========================================
# CUSTOM PERMISSIONS
# ==========================================

class IsOwnerOrReadOnly(BasePermission):
    """
    Allow everyone to read.
    Only the owner can modify an object.
    """

    def has_object_permission(self, request, view, obj):

        if request.method in SAFE_METHODS:
            return True

        return getattr(obj, 'user_id', None) == request.user.id


# ==========================================
# 1. CATEGORY VIEWSET
# ==========================================

class CategoryViewSet(viewsets.ModelViewSet):

    queryset = Category.objects.all()

    serializer_class = CategorySerializer


# ==========================================
# 2. AUTHOR VIEWSET
# ==========================================

class AuthorViewSet(viewsets.ModelViewSet):

    queryset = Author.objects.all()

    serializer_class = AuthorSerializer


# ==========================================
# 3. PUBLISHER VIEWSET
# ==========================================

class PublisherViewSet(viewsets.ModelViewSet):

    queryset = Publisher.objects.all()

    serializer_class = PublisherSerializer


# ==========================================
# 4. BOOK VIEWSET
# ==========================================

class BookViewSet(viewsets.ModelViewSet):

    queryset = Book.objects.prefetch_related(
        'authors',
        'categories'
    ).select_related('publisher')

    serializer_class = BookSerializer

    def get_permissions(self):

        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]

        return [IsAuthenticatedOrReadOnly()]


# ==========================================
# 5. CUSTOMER PROFILE VIEWSET
# ==========================================

class CustomerProfileViewSet(viewsets.ModelViewSet):

    serializer_class = CustomerProfileSerializer

    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        if self.request.user.is_staff:
            return CustomerProfile.objects.all()

        return CustomerProfile.objects.filter(
            user=self.request.user
        )

    def perform_create(self, serializer):

        serializer.save(user=self.request.user)


# ==========================================
# 6. CART VIEWSET
# ==========================================

class CartViewSet(viewsets.ModelViewSet):

    serializer_class = CartSerializer

    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        if self.request.user.is_staff:
            return Cart.objects.all()

        return Cart.objects.filter(
            user=self.request.user
        )

    def create(self, request, *args, **kwargs):

        cart, created = Cart.objects.get_or_create(
            user=request.user
        )

        serializer = self.get_serializer(cart)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created
            else status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'])
    def my_cart(self, request):

        cart, created = Cart.objects.get_or_create(
            user=request.user
        )

        serializer = self.get_serializer(cart)

        return Response(serializer.data)


# ==========================================
# 7. CART ITEM VIEWSET
# ==========================================

class CartItemViewSet(viewsets.ModelViewSet):

    serializer_class = CartItemSerializer

    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        if self.request.user.is_staff:
            return CartItem.objects.select_related('book', 'cart')

        return CartItem.objects.filter(
            cart__user=self.request.user
        ).select_related('book', 'cart')

    def perform_create(self, serializer):

        cart, created = Cart.objects.get_or_create(
            user=self.request.user
        )

        serializer.save(cart=cart)


# ==========================================
# 8. ORDER VIEWSET
# ==========================================

class OrderViewSet(viewsets.ModelViewSet):

    serializer_class = OrderSerializer

    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        if self.request.user.is_staff:
            return Order.objects.prefetch_related('items__book')

        return Order.objects.filter(
            user=self.request.user
        ).prefetch_related('items__book')

    def get_permissions(self):

        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAdminUser()]

        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():

            cart, created = Cart.objects.get_or_create(
                user=request.user
            )

            cart_items = list(
                CartItem.objects.select_for_update()
                .filter(cart=cart)
                .select_related('book')
            )

            if not cart_items:
                return Response(
                    {'error': 'Your cart is empty.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            total = Decimal('0.00')

            for item in cart_items:

                if item.quantity > item.book.stock_quantity:
                    return Response(
                        {
                            'error': (
                                f'Insufficient stock for '
                                f'{item.book.title}.'
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                total += item.book.price * item.quantity

            order = serializer.save(
                user=request.user,
                total_amount=total
            )

            for item in cart_items:

                OrderItem.objects.create(
                    order=order,
                    book=item.book,
                    quantity=item.quantity,
                    unit_price=item.book.price
                )

                Book.objects.filter(
                    pk=item.book.pk
                ).update(
                    stock_quantity=F('stock_quantity') - item.quantity
                )

            cart.items.all().delete()

        return Response(
            self.get_serializer(order).data,
            status=status.HTTP_201_CREATED
        )


# ==========================================
# 9. ORDER ITEM VIEWSET
# ==========================================

class OrderItemViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = OrderItemSerializer

    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        if self.request.user.is_staff:
            return OrderItem.objects.select_related('book', 'order')

        return OrderItem.objects.filter(
            order__user=self.request.user
        ).select_related('book', 'order')


# ==========================================
# 10. REVIEW VIEWSET
# ==========================================

class ReviewViewSet(viewsets.ModelViewSet):

    serializer_class = ReviewSerializer

    queryset = Review.objects.select_related(
        'user',
        'book'
    )

    def get_permissions(self):

        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrReadOnly()]

        return [IsAuthenticatedOrReadOnly()]

    def perform_create(self, serializer):

        serializer.save(user=self.request.user)
