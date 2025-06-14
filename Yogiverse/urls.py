from django.contrib import admin
from django.urls import path,include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('user_app.urls')),
    path('helper_app/', include('helper_app.urls')),
    path('chat_app/', include('chat_app.urls')),

]
