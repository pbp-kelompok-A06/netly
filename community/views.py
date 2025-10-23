from django.shortcuts import render, get_object_or_404, redirect
from community.models import Forum, Forum_Comment, Forum_Post
from community.forms import ForumForm, ForumCommentForm, ForumPostForm
from django.http import JsonResponse
from django.contrib.auth.models import User
from authentication_user.models import UserProfile

# fetch forum (done)
def fetch_forum(request):
    forum_list = Forum.objects.all().prefetch_related('member')

    for forum in forum_list:
        forum.is_member = forum.member.filter(id=request.user.profile.id).exists()

    context = {
        "data": forum_list
    }
    return render(request, "forum.html", context)

def fetch_forum_id(request, id_forum):
    forum_list = Forum.objects.filter(pk=id_forum, creator_id=request.user.profile).values('id', 'title', 'description')
    if forum_list:
        return JsonResponse({
            "success": True,
            "msg": "successfully fetched",
            "data": list(forum_list)
        })
    else:
        return JsonResponse({
            "success": True,
            "msg": "Failed to fetch",
            "data": []
        })


# fetch post by id forum
def fetch_post_id(request, id_forum):
    post_list = Forum_Post.objects.filter(forum_id=id_forum)
    if post_list:

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                "success": True,
                "msg": "successfully fetch posts.",
                "data": post_list
            
            })
    
    context = {
        "id_forum": id_forum,
        "data_post": post_list
    }
    return render(request, "forum_post.html", context)


# fetch comment by id post
def fetch_comment_id(request, id_forum, id_forum_post):
    post_list = Forum_Comment.objects.filter(forum_id=id_forum, forum_post_id=id_forum_post)
    context = {
        "data": post_list
    }
    return 0

# create forum (done)
def create_forum(request):
    form = ForumForm()
    if request.method == "POST":
        form = ForumForm(request.POST)
        if form.is_valid():
            forum_entry = form.save(commit=False)
            forum_entry.creator_id = request.user.profile
            forum_entry.save()
            forum_entry.member.add(request.user.profile)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    "success": True,
                    "msg": "forum created."
                })
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    "success": False,
                    "msg": "failed created."
                })

# join forum (done)
def join_forum(request):
    if request.method == "POST":
        forum = get_object_or_404(Forum, pk = request.POST.get('id_forum'))
        if request.user.profile not in forum.member.all():
            forum.member.add(request.user.profile)
            return JsonResponse({
                "success": True,
                "msg": f"Successfully joined forum {forum.title}"
            })
        else:
            return JsonResponse({
                "success": False,
                "msg": "You are already joined."
            })




# create post

def create_post(request, id_forum):
    form = ForumPostForm()
    if request.method == "POST":
        form = ForumPostForm(request.POST)
        if form.is_valid():
            forum_entry = form.save(commit=False)
            forum_entry.user_id = request.user.profile
            forum = get_object_or_404(Forum, id=id_forum)
            forum_entry.forum_id = forum
            forum_entry.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    "success": True,
                    "msg": "Post created."
                })
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    "success": False,
                    "msg": "failed to create a post."
                })


# create_comment

# def create_comment(request, id_forum, id_forum_post):
#     form = ForumCommentForm()
#     if request.method == "POST":
#         form = ForumCommentForm(request.POST)
#         if form.is_valid():
#             forum_entry = form.save(commit=False)
#             forum_entry.user_id = request.user.profile.id
#             forum_entry.forum_id = id_forum
#             forum_entry.forum_post_id = id_forum_post
#             forum_entry.save()
    
#     context = {
#         "form": form
#     }

#     return 0


# update forum by id creator
def update_forum(request, id_forum):
    forum_data = get_object_or_404(Forum, id=id_forum, creator_id=request.user.profile)
    if request.method == "POST":
        form = ForumForm(request.POST, instance=forum_data)
        if form.is_valid():
            form.save()
            return JsonResponse({
                "success": True,
                "msg": "Successfully updated!"
            })
        else:
            return JsonResponse({
                "success": False,
                "msg": "Failed to update"
            })
    

# delete forum by id creator (done)
def delete_forum(request, id_forum):
    forum_data = get_object_or_404(Forum, creator_id=request.user.profile, pk=id_forum)
    forum_data.delete()
    return redirect("community:forum")

# delete post by id user and id_forum
def delete_forum_post(request, id_forum):
    forum_post_data = get_object_or_404(Forum_Post, forum_id=id_forum, )
    if request.method == "POST":
        forum_post_data.delete()
    
    return 0

# delete comment
# def delete_forum_comment(request, id_forum, id_post):
#     forum_post_data = get_object_or_404(Forum_Post, forum_id=id_forum, )
#     if request.method == "POST":
#         forum_post_data.delete()
    
#     return 0



def test(request):
    print(request.user.profile)
    return render(request,"forum_post.html")

