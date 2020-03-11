"""yatube URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
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
from django.urls import path, include
from django.contrib.flatpages import views
from django.conf.urls import handler404, handler500
from django.conf import settings
from django.conf.urls.static import static

handler404 = "posts.views.page_not_found" # noqa
handler500 = "posts.views.server_error" # noqa
 
urlpatterns = [

    # flatpages
    path("about/", include("django.contrib.flatpages.urls")),

    # user registration and authentication is in users app
    path('auth/', include('users.urls')),

    # if authentication-related URL not found in users, search django.contrib.auth
    path('auth/', include('django.contrib.auth.urls')),

    # admin site
    path('admin/', admin.site.urls),

    #flatpages
    path('about-author/', views.flatpage, {'url': '/about-author/'}, name='author'),
    path('about-spec/', views.flatpage, {'url': '/about-spec/'}, name='spec'),
    
    # site home page views are in posts app
    path('', include('posts.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)