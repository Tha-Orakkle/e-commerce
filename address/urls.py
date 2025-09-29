from django.urls import path

from .api.v1.routes import (
    CityListView,
    CountryListView,
    StateListView,
    ShippingAddressListCreateView,
    ShippingAddressDetailView
)


urlpatterns = [
    path('address/', ShippingAddressListCreateView.as_view(), name='shipping-addresses'),
    path('address/<str:address_id>/', ShippingAddressDetailView.as_view(), name='shipping-address'),
    path('countries/', CountryListView.as_view(), name="countries"),
    path('states/', StateListView.as_view(), name="states"),
    path('cities/', CityListView.as_view(), name="cities")
]