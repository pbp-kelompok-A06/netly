from django.urls import path
from community.views import test, fetch_forum, create_forum, delete_forum, join_forum, fetch_forum_id, update_forum, fetch_post_id, create_post
app_name = 'community'

urlpatterns = [
    path('', test, name="tes"),
    path('forum/', fetch_forum, name="forum" ),
    path('forum/<uuid:id_forum>/', fetch_forum_id, name="fetch_forum_id" ),
    path('forum/post/<uuid:id_forum>/', fetch_post_id, name="fetch_post_id" ),
    path('create-post/<uuid:id_forum>/', create_post, name="create_post"),
    path('create-forum/', create_forum, name="create_forum"),
    path('update-forum/<uuid:id_forum>/', update_forum, name="update_forum" ),
    path('delete-forum/<uuid:id_forum>', delete_forum, name="delete_forum"),
    path('join-forum/', join_forum, name="join_forum"),
]