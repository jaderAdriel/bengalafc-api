from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from .views import hello_world, pag2
from apps.users.api.router import router as users_router

router = routers.DefaultRouter()
router.register(r'users', users_router, basename='users')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('hello/', hello_world, name='hello_world'),
    path('pag2/', pag2, name='pag2'),
    
    # API URLs
    path('api/', include(router.urls)),
    
    # OAuth2 URLs
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
]
