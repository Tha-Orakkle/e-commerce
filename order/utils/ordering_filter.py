from django.db.models import Case, When, Value, IntegerField
from rest_framework.filters import OrderingFilter


class SmartOrderingFilter(OrderingFilter):
    """
    Custom ordering filter that allows for smart ordering of queryset.
    It will order by 'status' first, and then 'created'.
    """

    def filter_queryset(self, request, queryset, view):
        ordering_params = request.query_params.getlist(self.ordering_param)
        valid_fields = getattr(view, 'ordering_fields', [])

        if ordering_params:
            fields = [field.lstrip('-') for field in ordering_params]
            if all(field in valid_fields for field in fields):
                return super().filter_queryset(request, queryset, view)
        
        return queryset.annotate(
            priority=Case(
                When(status='PENDING', then=Value(0)),
                When(status='PROCESSING', then=Value(1)),
                default=Value(2),
                output_field=IntegerField()
            )
        ).order_by('priority', 'created_at')
