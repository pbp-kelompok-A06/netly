from django.urls import path
from community.views import test
app_name = 'community'

urlpatterns = [
    path('', test, name="tes")
]