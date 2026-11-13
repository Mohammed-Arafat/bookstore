
import django_filters
from .models import Book


class BookFilter(django_filters.FilterSet):

    # Filter books by category slug
    category = django_filters.CharFilter(
        field_name='categories__slug',
        lookup_expr='iexact'
    )

    # Filter books by publisher ID
    publisher = django_filters.NumberFilter(
        field_name='publisher__id'
    )

    # Filter books by author ID
    author = django_filters.NumberFilter(
        field_name='authors__id'
    )

    # Filter books by minimum and maximum price
    min_price = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='gte'
    )

    max_price = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='lte'
    )

    # Filter books based on stock availability
    in_stock = django_filters.BooleanFilter(
        method='filter_in_stock'
    )

    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(stock_quantity__gt=0)

        return queryset.filter(stock_quantity=0)

    class Meta:
        model = Book
        fields = [
            'category',
            'publisher',
            'author',
            'min_price',
            'max_price',
            'in_stock',
        ]
