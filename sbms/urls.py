from django.contrib import admin
from django.urls import path,include
from core.views import homeView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', homeView.as_view(), name='home'),
    path('accounts/', include('accounts.urls')),
    path('transactions/', include('transactions.urls')),
    path('features/', include('features.urls')),
]