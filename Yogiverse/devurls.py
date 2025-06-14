from django.contrib import admin
from django.urls import path,include
from django.conf import settings

from django.conf.urls.static import static


urlpatterns = [
    path('', include('user_app.urls')),
    path('helper_app/', include('helper_app.urls')),
    path('chat_app/', include('chat_app.urls')),
    path('admin/', admin.site.urls),
    path('', include('post_app.urls')),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# urlpatterns += static(settings.EXPORT_URL, document_root=settings.EXPORT_ROOT)
# urlpatterns += static(settings.PDF_FILES_URL, document_root=settings.PDF_FILES_ROOT)
