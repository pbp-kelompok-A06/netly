from django.shortcuts import render, get_object_or_404, redirect
from community.models import Forum, Forum_Post
from community.forms import ForumForm, ForumPostForm
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

# fetch forum (done)
@login_required(login_url="authentication_user:login")
def fetch_forum(request):
    forum_list = Forum.objects.all().prefetch_related('member')

    json_data = []
    for forum in forum_list:
        forum.is_member = forum.member.filter(id=request.user.profile.id).exists()
        json_data.append({
            "id": forum.id,
            "creator_name": forum.creator_id.user.username,
            "creator_id": forum.creator_id.id,
            "title": forum.title,
            "description": forum.description,
            "member_count": forum.member.count(),
            "is_member": forum.is_member,
            "created_at": forum.created_at,
            "updated_at": forum.updated_at
        })
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if len(forum_list) != 0:

            return JsonResponse({
                "success": True,
                "msg": "Successfully fetched",
                "data": json_data
            }, safe=False)

    context = {
        "data": forum_list
    }
    return render(request, "forum.html", context)

# fetch forum by id (done)
@login_required(login_url="authentication_user:login")
def fetch_forum_id(request, id_forum):
    forum_list = Forum.objects.filter(pk=id_forum, creator_id=request.user.profile).values('id', 'creator_id', 'title', 'description', 'created_at', 'updated_at')
    if forum_list:
        return JsonResponse({
            "success": True,
            "msg": "successfully fetched",
            "data": list(forum_list)
        })
    else:
        return JsonResponse({
            "success": False,
            "msg": "Failed to fetch",
            "data": []
        })


# fetch forum by creator (done)
@login_required(login_url="authentication_user:login")
def fetch_forum_creator(request):
    forum_list = Forum.objects.filter(creator_id=request.user.profile).values('id', 'creator_id', 'title', 'description', 'created_at', 'updated_at')
    if forum_list:
        return JsonResponse({
            "success": True,
            "msg": "successfully fetched",
            "data": list(forum_list)
        })
    else:
        return JsonResponse({
            "success": False,
            "msg": "Failed to fetch",
            "data": []
        })

# fetch forum that user joins (done)
@login_required(login_url="authentication_user:login")
def fetch_forum_joined(request):
    forum_list = Forum.objects.filter(member=request.user.profile).values('id', 'creator_id', 'title', 'description', 'created_at', 'updated_at')
    if forum_list:
        return JsonResponse({
            "success": True,
            "msg": "successfully fetched",
            "data": list(forum_list)
        })
    else:
        return JsonResponse({
            "success": False,
            "msg": "Failed to fetch",
            "data": []
        })

# fetch post recently that user joined (done)
@login_required(login_url="authentication_user:login")
def fetch_post_recently(request, limit=1):
    if limit <= 0:
        limit = 1
    recent_posts = Forum_Post.objects.filter(forum_id__member = request.user.profile).select_related('user_id', 'forum_id').order_by('-created_at')[:limit]

    json_data = []

    for post in recent_posts:
        json_data.append({
            "id": str(post.id),
            "header": post.header,
            "content": post.content,
            "created_at": post.created_at,
            "forum_name": post.forum_id.title,
            "user": {
                "id": str(post.user_id.id),
                "username": post.user_id.user.username 
            }
        })

    return JsonResponse({
        "success": True,
        "msg": "Successfully fetched recent posts",
        "data": json_data
    }, safe=False)
    



# fetch post by id forum (done)
@login_required(login_url="authentication_user:login")
def fetch_post_id(request, id_forum):
    forum_data = get_object_or_404(Forum, id=id_forum)
    post_list = Forum_Post.objects.filter(forum_id=forum_data).select_related('user_id').order_by('-created_at')
    
    if request.user.profile not in forum_data.member.all() and request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return HttpResponse("<script>alert('You are not a member of this forum.'); window.location.href='/community/';</script>")
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if request.user.profile not in forum_data.member.all():
            return JsonResponse({
                "success": False,
                "msg": "Not a member",
                "data": []
            })
        data = []
        for post in post_list:
            try:
                username = post.user_id.user.username
            except Exception:
                username = "None"

            data.append({
                "id": str(post.id),
                "header": post.header,
                "content": post.content,
                "created_at": post.created_at.isoformat() if post.created_at else None,
                "user": {
                    "id": str(post.user_id.id),
                    "username": username
                }
            })
        if len(data) != 0:
            return JsonResponse({
                "success": True,
                "msg": "successfully fetched posts.",
                "data": data,
                "current_user_id": str(request.user.profile.id)
            })
        return JsonResponse({
            "success": False,
            "msg": "data is empty",
            "data": data
        })
    

    context = {
        "id_forum": id_forum,
        "forum_name": forum_data.title
    }
    return render(request, "forum_post.html", context)


# fetch post by id forum and user created (done)
@login_required(login_url="authentication_user:login")
def fetch_post_id_user(request, id_forum):
    forum_data = get_object_or_404(Forum, id=id_forum)
    post_list = Forum_Post.objects.filter(forum_id=forum_data, user_id=request.user.profile).select_related('user_id').order_by('-created_at')
    
    if request.user.profile not in forum_data.member.all() and request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return HttpResponse("<script>alert('You are not a member of this forum.'); window.location.href='/community/';</script>")
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if request.user.profile not in forum_data.member.all():
            return JsonResponse({
                "success": False,
                "msg": "Not a member",
                "data": []
            })
        data = []
        for post in post_list:
            try:
                username = post.user_id.user.username
            except Exception:
                username = "None"

            data.append({
                "id": str(post.id),
                "header": post.header,
                "content": post.content,
                "created_at": post.created_at.isoformat() if post.created_at else None,
                "user": {
                    "id": str(post.user_id.id),
                    "username": username
                }
            })
        if len(data) != 0:
            return JsonResponse({
                "success": True,
                "msg": "successfully fetched posts.",
                "data": data,
                "current_user_id": str(request.user.profile.id)
            })
        return JsonResponse({
            "success": False,
            "msg": "data is empty",
            "data": data
        })
    

    context = {
        "id_forum": id_forum,
        "forum_name": forum_data.title
    }
    return render(request, "forum_post.html", context)



# create forum (done)
@csrf_exempt
@login_required(login_url="authentication_user:login")
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
@login_required(login_url="authentication_user:login")
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
# unjoin forum (done)
@login_required(login_url="authentication_user:login")
def unjoin_forum(request):
    if request.method == "POST":
        forum = get_object_or_404(Forum, pk = request.POST.get('id_forum'))
        if request.user.profile in forum.member.all():
            if forum.creator_id == request.user.profile:
                forum.delete()
            else:
                forum.member.remove(request.user.profile)
            return JsonResponse({
                "success": True,
                "msg": f"Successfully unjoined forum {forum.title}"
            })
        else:
            return JsonResponse({
                "success": False,
                "msg": "You are already not part of the forum."
            })




# create post (done)
@csrf_exempt
@login_required(login_url="authentication_user:login")
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


# update forum by id creator (done)
@login_required(login_url="authentication_user:login")
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
@csrf_exempt
@login_required(login_url="authentication_user:login")
def delete_forum(request, id_forum):
    
    forum_data = get_object_or_404(Forum, creator_id=request.user.profile, pk=id_forum)
    forum_data.delete()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            "success": True,
            "msg": "Successfully deleted."
        }) 
    return redirect("community:forum")


# delete post by id user and id_post (done)
@login_required(login_url="authentication_user:login")
def delete_forum_post(request, id_post):
    forum_post_data = get_object_or_404(Forum_Post, id=id_post, user_id=request.user.profile)
    if request.method == "POST":
        forum_post_data.delete()
        return JsonResponse({
            "success": True,
            "msg": "Successfully deleted."
        })
    
    return JsonResponse({
        "success": False,
        "msg": "Failed to delete"
    })

