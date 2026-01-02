from django.urls import path

from shop.api.v1.routes import ShopListView, ShopDetailView


urlpatterns = [
    path('shops/', ShopListView.as_view(), name='shop-list'),
    path('shops/<str:shop_id>/', ShopDetailView.as_view(), name='shop-detail')
]