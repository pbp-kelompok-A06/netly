from django.urls import path
from community.views import fetch_forum, fetch_forum_creator, fetch_post_recently, fetch_forum_joined, fetch_post_id_user, create_forum, delete_forum, join_forum, fetch_forum_id, update_forum, fetch_post_id, create_post, unjoin_forum, delete_forum_post
app_name = 'community'

urlpatterns = [
    path('', fetch_forum, name="forum" ),
    path('forum/<uuid:id_forum>/', fetch_forum_id, name="fetch_forum_id" ),
    path('forum/my-forum', fetch_forum_creator, name="fetch_forum_creator" ),
    path('forum/joined', fetch_forum_joined, name="fetch_forum_joined" ),
    path('forum/post/<uuid:id_forum>/', fetch_post_id, name="fetch_post_id" ),
    path('forum/post/<uuid:id_forum>/user', fetch_post_id_user, name="fetch_post_id_user" ),
    path('create-post/<uuid:id_forum>/', create_post, name="create_post"),
    path('create-forum/', create_forum, name="create_forum"),
    path('update-forum/<uuid:id_forum>/', update_forum, name="update_forum" ),
    path('delete-forum/<uuid:id_forum>/', delete_forum, name="delete_forum"),
    path('delete-forum-post/<uuid:id_post>/', delete_forum_post, name="delete_forum_post"),
    path('join-forum/', join_forum, name="join_forum"),
    path('unjoin-forum/', unjoin_forum, name="unjoin_forum"),

    path('forum/post/recent/<int:limit>/', fetch_post_recently, name="fetch_post_recently"),
]