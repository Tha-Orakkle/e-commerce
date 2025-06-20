from django.urls import path

from .api.v1.routes.shipping_address import ShippingAddressView, ShippingAddressDetailView
from .api.v1.routes.country import CountryView
from .api.v1.routes.state import StateView
from .api.v1.routes.city import CityView


urlpatterns = [
    path('address/', ShippingAddressView.as_view(), name='shipping-addresses'),
    path('address/<str:address_id>/', ShippingAddressDetailView.as_view(), name='shipping-address'),
    path('countries/', CountryView.as_view(), name="countries"),
    path('states/', StateView.as_view(), name="states"),
    path('cities/', CityView.as_view(), name="cities"),
]