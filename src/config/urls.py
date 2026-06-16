from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from .views import hello_world, pag2, signup_view
from apps.users.api.router import router as users_router
from apps.football.api.router import router as football_router
from apps.ranking.api.router import router as ranking_router
from apps.scores.api.router import router as scores_router

urlpatterns = [
    path('admin/', admin.site.urls),
    path('hello/', hello_world, name='hello_world'),
    path('pag2/', pag2, name='pag2'),
    
    # Web Authentication URLs
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/signup/', signup_view, name='signup'),
    
    # API URLs
    path('api/', include(users_router.urls)),
    path('api/', include(football_router.urls)),
    path('api/', include(ranking_router.urls)),
    path('api/', include(scores_router.urls)),
    
    # API Schema & Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # OAuth2 URLs
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
