from django.shortcuts import render, get_object_or_404, redirect
from community.models import Forum, Forum_Post
from community.forms import ForumForm, ForumPostForm
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required

# fetch forum (done)
@login_required(login_url="/login")
def fetch_forum(request):
    forum_list = Forum.objects.all().prefetch_related('member')

    for forum in forum_list:
        forum.is_member = forum.member.filter(id=request.user.profile.id).exists()

    context = {
        "data": forum_list
    }
    return render(request, "forum.html", context)

# fetch forum by id (done)
@login_required(login_url="/login")
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
            "success": False,
            "msg": "Failed to fetch",
            "data": []
        })


# fetch post by id forum (done)
@login_required(login_url="/login")
def fetch_post_id(request, id_forum):
    forum_data = get_object_or_404(Forum, id=id_forum)
    post_list = Forum_Post.objects.filter(forum_id=forum_data).select_related('user_id').order_by('-created_at')
    
    if request.user.profile not in forum_data.member.all():
        return HttpResponse("<script>alert('You are not a member of this forum.'); window.location.href='/community/forum/';</script>")
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
    
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
@login_required(login_url="/login")
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
@login_required(login_url="/login")
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
@login_required(login_url="/login")
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
@login_required(login_url="/login")
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
@login_required(login_url="/login")
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
@login_required(login_url="/login")
def delete_forum(request, id_forum):
    forum_data = get_object_or_404(Forum, creator_id=request.user.profile, pk=id_forum)
    forum_data.delete()
    return redirect("community:forum")

# delete post by id user and id_post (done)
@login_required(login_url="/login")
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

