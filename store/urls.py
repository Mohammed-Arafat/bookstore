
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

router.register('categories', CategoryViewSet)
router.register('authors', AuthorViewSet)
router.register('publishers', PublisherViewSet)
router.register('books', BookViewSet)
router.register('profiles', CustomerProfileViewSet)
router.register('carts', CartViewSet)
router.register('cart-items', CartItemViewSet)
router.register('orders', OrderViewSet)
router.register('order-items', OrderItemViewSet)
router.register('reviews', ReviewViewSet)

urlpatterns = router.urls
