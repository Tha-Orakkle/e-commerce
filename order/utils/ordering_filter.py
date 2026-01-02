from django.db.models import Case, When, Value, IntegerField
from rest_framework.filters import OrderingFilter

import django_filters

from order.models import Order

class OrderFilter(django_filters.FilterSet):
    """
    Custom filter for Order model to filter by status.
    """
    status = django_filters.CharFilter(field_name='status', lookup_expr='exact', method='filter_status')

    def filter_status(self, queryset, name, value):
        """
        Filter queryset by status.
        """
        if value:
            return queryset.filter(**{name: value.strip().upper()})
        return queryset

    class Meta:
        model = Order
        fields = ['status']


class SmartOrdering(OrderingFilter):
    """
    Custom ordering model that allows for smart ordering of queryset.
    It will order by 'status' first, and then 'created_at'.
    """

    def filter_queryset(self, request, queryset, view):
        ordering_params = request.query_params.getlist(self.ordering_param)
        valid_fields = getattr(view, 'ordering_fields', [])

        if ordering_params:
            normalized = []
            for param in ordering_params:
                prefix = '-' if param.strip().startswith('-') else ''
                field_name = param.strip().lstrip('-').lower()
                if field_name in valid_fields:
                    normalized.append(f"{prefix}{field_name}")
                else:
                    break
            else: # executes if loop completes 
                # All ordering params are valid. Override the query params
                mutable = request.query_params._mutable
                request.query_params._mutable = True
                request.query_params.setlist(self.ordering_param, normalized)
                request.query_params._mutable = mutable
                return super().filter_queryset(request, queryset, view)

        return queryset.annotate(
            priority=Case(
                When(status='PENDING', then=Value(0)),
                When(status='PROCESSING', then=Value(1)),
                When(status='SHIPPED', then=Value(2)),
                default=Value(3),
                output_field=IntegerField()
            )
        ).order_by('priority', 'created_at')
