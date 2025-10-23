from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from authentication_user.models import UserProfile
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
import json

# untuk call register.html
def register_view(request):
    if request.user.is_authenticated:
        return redirect('homepage') # kalau  berhasil login, langsung ke homepage
    return render(request, "register.html")

# untuk call login.html
def login_view(request):
    if request.user.is_authenticated:
        return redirect('homepage') 
    return render(request, "login.html")

@login_required(login_url='/login') 
def logout_view(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('authentication_user:login')    # redirect ke home page

@require_POST 
def register_ajax(request):
    # handle register with ajax
    try:
        # ambil data json
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password1')
        password2 = data.get('password2')
        full_name = data.get('full_name')
        location = data.get('location')
        profile_picture = data.get('profile_picture')


        # validate username, password, dan full name
        if not all([username, password, password2, full_name]):
            return JsonResponse({'status': 'error', 'message': 'Semua field wajib diisi.'}, status=400)

        if password != password2:
            return JsonResponse({'status': 'error', 'message': 'Passwords tidak cocok.'}, status=400)
        
        if User.objects.filter(username=username).exists():
            return JsonResponse({'status': 'error', 'message': 'Username ini sudah dipakai.'}, status=400)

        # create user baru
        user = User.objects.create_user(username=username, password=password)
        
        userProfile = UserProfile.objects.create(
            user = user,
            fullname=full_name,
            location=location,
            profile_picture=profile_picture
        )

        user.save()
        userProfile.save()

        # automatically login after user berhasil regist
        login(request, user)

        # success
        return JsonResponse({'status': 'success', 'message': 'Registrasi berhasil!'})

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Format data tidak valid.'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Terjadi kesalahan: {str(e)}'}, status=500)


@require_POST 
def login_ajax(request):
    # handle login user via ajax
    try:
        # ambil data JSON yang dikirim dari script di login_html
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        # kalau username atau password kosong
        if not all([username, password]):
            return JsonResponse({'status': 'error', 'message': 'Username dan password wajib diisi.'}, status=400)

        # autentikasi user
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # if usernya valid, bisa login
            login(request, user)
            # success response
            return JsonResponse({'status': 'success', 'message': 'Login berhasil!'})
        else:
            # kalau user ga valid
            return JsonResponse({'status': 'error', 'message': 'Username atau password salah.'}, status=400)

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Format data tidak valid.'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Terjadi kesalahan: {str(e)}'}, status=500)


def make_admin(request):
    data_admin = [
        {
            "username":"admin_bagus",
            "password":"admin_bagus",
            "fullname":"bagus"
        },
        {
            "username":"admin_dewa",
            "password":"admin_dewa",
            "fullname":"dewa"
        },
        {
            "username":"admin_halo",
            "password":"admin_halo",
            "fullname":"halo"
        }
    ]

    for data in data_admin:
        profile = UserProfile.objects.filter(fullname=data.get("fullname"))
        if profile:
            continue
        else:
            user = User.objects.create_user(username=data.get("username"), password=data.get("password"))
            userProfile = UserProfile.objects.create(
                user = user,
                fullname=data.get("fullname"),
                role="admin"
            )

            user.save()
            userProfile.save()
    return HttpResponse("halo")
    
