from django.urls import path
from authentication_user.views import login_view, logout_view, register_view, login_ajax, register_ajax, make_admin


app_name = 'authentication_user'

# uncomment pas udah ada views + urls dari app ini aja yaa
urlpatterns = [
    path('login/', login_view, name="login"),
    path('logout/', logout_view, name="logout"),
    path('register/', register_view, name="register"),
    path('register-ajax/', register_ajax, name="register_ajax"),
    path('login-ajax/', login_ajax, name="login_ajax"),
    path('make-admin', make_admin, name="make_admin")
]