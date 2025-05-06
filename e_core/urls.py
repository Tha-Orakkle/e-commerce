from django.contrib import admin
from django.conf.urls import handler404, handler500
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from common.utils.error_handlers import custom_404_handler, custom_500_handler

# Custom error handlers at django level
handler404 = custom_404_handler
handler500 = custom_500_handler


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/v1/', include('user.urls')),
    path('api/v1/', include('product.urls')),
]
