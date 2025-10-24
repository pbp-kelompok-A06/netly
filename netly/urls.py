"""
URL configuration for netly project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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

urlpatterns = [
    path('', include('homepage.urls', namespace='homepage')),
    path('community/', include('community.urls')),
    path('', include('homepage.urls')),
    path('booking/', include('booking.urls')),
    path('event/', include('event.urls')),
    path('', include('authentication_user.urls')),
    path('lapangan/', include('admin_lapangan.urls'))
    # path('', include('authentication_user.urls')) --> uncomment pas udah ada views + urls dari app ini aja yaa
]

