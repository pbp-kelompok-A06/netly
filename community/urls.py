from django.urls import path
from community.views import test, fetch_forum, create_forum, delete_forum, join_forum
app_name = 'community'

urlpatterns = [
    path('', test, name="tes"),
    path('forum/', fetch_forum, name="forum" ),
    path('create-forum/', create_forum, name="create_forum"),
    path('delete-forum/<uuid:id_forum>', delete_forum, name="delete_forum"),
    path('join-forum/', join_forum, name="join_forum")
]