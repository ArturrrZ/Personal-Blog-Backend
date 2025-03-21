from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from api.views import CreateUserView, LoginView, LogoutView, RefreshTokenView, CheckAuthenticationView
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/user/register/', CreateUserView.as_view(), name='register'),
    path('api/user/login/', LoginView.as_view(), name='login'),
    path('api/user/logout/', LogoutView.as_view(), name='logout'),
    path('api/user/refresh_token/', RefreshTokenView.as_view(), name='refresh_token'),
    path('api/user/check-auth/', CheckAuthenticationView.as_view(), name='check-auth'),
    path('api/', include('api.urls'))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
