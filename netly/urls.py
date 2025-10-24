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
    path('', include(('homepage.urls', 'homepage'), namespace='homepage')),
    path('community/', include('community.urls')),
<<<<<<< HEAD
    path('booking/', include(('booking.urls', 'booking'), namespace='booking')),           
    path('admin-lapangan/', include(('admin_lapangan.urls', 'admin_lapangan'), namespace='admin_lapangan')),
    path('event/', include(('event.urls', 'event'), namespace='event')),
    path('authentication_user/', include(('authentication_user.urls', 'authentication_user'), namespace='authentication_user')),
=======
    path('', include('homepage.urls')),
    path('booking/', include('booking.urls')),
    path('event/', include('event.urls')),
    path('', include('authentication_user.urls')),
    path('lapangan/', include('admin_lapangan.urls'))
    # path('', include('authentication_user.urls')) --> uncomment pas udah ada views + urls dari app ini aja yaa
>>>>>>> b0e7c14c596c2fc59cab014026bfe81c955e47e5
]

