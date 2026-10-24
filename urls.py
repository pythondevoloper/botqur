"""
URL configuration for BotQur project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.urls import include, path
from django.views.static import serve
from django.conf.urls.static import static


urlpatterns = [
    path("admin/", admin.site.urls),

    path("", include("frontend.urls")),


    path(
        "_next/<path:path>",
        serve,
        {"document_root": settings.BASE_DIR / "frontend" / "nextassets" / "_next"},
    ),
    path(
        "brand/<path:path>",
        serve,
        {"document_root": settings.BASE_DIR / "frontend" / "nextassets" / "brand"},
    ),
    path(
        "botqur-media/<path:path>",
        serve,
        {"document_root": settings.BASE_DIR / "frontend" / "nextassets" / "botqur-media"},
    ),
    path(
        "favicon.ico",
        serve,
        {
            "document_root": settings.BASE_DIR / "frontend" / "nextassets",
            "path": "favicon.ico",
        },
    ),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)