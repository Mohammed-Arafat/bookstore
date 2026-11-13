from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    AuthorViewSet,
    PublisherViewSet,
    BookViewSet,
    CustomerProfileViewSet,
    CartViewSet,
    CartItemViewSet,
    OrderViewSet,
    OrderItemViewSet,
    ReviewViewSet
)

router = DefaultRouter()

router.register('categories', CategoryViewSet, basename='category')
router.register('authors', AuthorViewSet, basename='author')
router.register('publishers', PublisherViewSet, basename='publisher')
router.register('books', BookViewSet, basename='book')
router.register('profiles', CustomerProfileViewSet, basename='profile')
router.register('carts', CartViewSet, basename='cart')
router.register('cart-items', CartItemViewSet, basename='cartitem')
router.register('orders', OrderViewSet, basename='order')
router.register('order-items', OrderItemViewSet, basename='orderitem')
router.register('reviews', ReviewViewSet, basename='review')

urlpatterns = router.urls