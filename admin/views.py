from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Lapangan, JadwalLapangan
from .forms import LapanganForm, JadwalLapanganForm

def is_admin(user):
    return hasattr(user, 'profile') and user.profile.role == 'admin_lapangan'

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('authentication_user:login')
        if not is_admin(request.user):
            return HttpResponseForbidden("You don't have permission to access this page.")
        return view_func(request, *args, **kwargs)
    return wrapper

# Dashboard
@admin_required
def admin_dashboard(request):
    recent_lapangan = Lapangan.objects.filter(admin=request.user)[:5]
    
    context = {
        'recent_lapangan': recent_lapangan,
    }
    return render(request, 'admin_lapangan/dashboard.html', context)

# Lapangan CRUD
@admin_required
def lapangan_list(request):
    search_query = request.GET.get('search', '')
    lapangan_list = Lapangan.objects.filter(admin=request.user)
    
    if search_query:
        lapangan_list = lapangan_list.filter(
            lapangan_list.filter(name__icontains=search_query, location__icontains=search_query)
        )
    
    paginator = Paginator(lapangan_list, 10)
    page_number = request.GET.get('page')
    lapangan = paginator.get_page(page_number)
    
    context = {
        'lapangan': lapangan,
        'search_query': search_query,
    }
    return render(request, 'admin_lapangan/lapangan_list.html', context)

@admin_required
def lapangan_create(request):
    if request.method == 'POST':
        form = LapanganForm(request.POST, request.FILES)
        if form.is_valid():
            lapangan = form.save(commit=False)
            lapangan.admin = request.user
            lapangan.save()
            messages.success(request, 'Lapangan berhasil ditambahkan!')
            return redirect('admin_lapangan:lapangan_list')
    else:
        form = LapanganForm()
    
    return render(request, 'admin_lapangan/lapangan_form.html', {'form': form, 'action': 'Create'})

@admin_required
def lapangan_edit(request, lapangan_id):
    lapangan = get_object_or_404(Lapangan, id=lapangan_id, admin=request.user)
    
    if request.method == 'POST':
        form = LapanganForm(request.POST, request.FILES, instance=lapangan)
        if form.is_valid():
            form.save()
            messages.success(request, 'Lapangan berhasil diupdate!')
            return redirect('admin_lapangan:lapangan_list')
    else:
        form = LapanganForm(instance=lapangan)
    
    return render(request, 'admin_lapangan/lapangan_form.html', {
        'form': form, 
        'action': 'Edit',
        'lapangan': lapangan
    })

@admin_required
@require_http_methods(["POST", "DELETE"])
def lapangan_delete(request, lapangan_id):
    lapangan = get_object_or_404(Lapangan, id=lapangan_id, admin=request.user)
    lapangan_name = lapangan.name
    lapangan.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': f'{lapangan_name} berhasil dihapus!'})
    
    messages.success(request, f'{lapangan_name} berhasil dihapus!')
    return redirect('admin_lapangan:lapangan_list')

@admin_required
def lapangan_detail(request, lapangan_id):
    lapangan = get_object_or_404(Lapangan, id=lapangan_id, admin=request.user)
    jadwal = lapangan.jadwal.all().order_by('tanggal', 'start_main')
    
    context = {
        'lapangan': lapangan,
        'jadwal': jadwal,
    }
    return render(request, 'admin_lapangan/lapangan_detail.html', context)

# Jadwal CRUD
@admin_required
def jadwal_list(request, lapangan_id):
    lapangan = get_object_or_404(Lapangan, id=lapangan_id, admin=request.user)
    jadwal = lapangan.jadwal.all().order_by('tanggal', 'start_main')
    
    context = {
        'lapangan': lapangan,
        'jadwal': jadwal,
    }
    return render(request, 'admin_lapangan/jadwal_list.html', context)

@admin_required
def jadwal_create(request, lapangan_id):
    lapangan = get_object_or_404(Lapangan, id=lapangan_id, admin=request.user)
    
    if request.method == 'POST':
        form = JadwalLapanganForm(request.POST)
        if form.is_valid():
            jadwal = form.save(commit=False)
            jadwal.lapangan = lapangan
            jadwal.save()
            messages.success(request, 'Jadwal berhasil ditambahkan!')
            return redirect('admin_lapangan:jadwal_list', lapangan_id=lapangan_id)
    else:
        form = JadwalLapanganForm()
    
    return render(request, 'admin_lapangan/jadwal_form.html', {
        'form': form,
        'action': 'Create',
        'lapangan': lapangan
    })

@admin_required
def jadwal_edit(request, jadwal_id):
    jadwal = get_object_or_404(JadwalLapangan, id=jadwal_id, lapangan__admin=request.user)
    
    if request.method == 'POST':
        form = JadwalLapanganForm(request.POST, instance=jadwal)
        if form.is_valid():
            form.save()
            messages.success(request, 'Jadwal berhasil diupdate!')
            return redirect('admin_lapangan:jadwal_list', lapangan_id=jadwal.lapangan.id)
    else:
        form = JadwalLapanganForm(instance=jadwal)
    
    return render(request, 'admin_lapangan/jadwal_form.html', {
        'form': form,
        'action': 'Edit',
        'lapangan': jadwal.lapangan,
        'jadwal': jadwal
    })

@admin_required
@require_http_methods(["POST", "DELETE"])
def jadwal_delete(request, jadwal_id):
    jadwal = get_object_or_404(JadwalLapangan, id=jadwal_id, lapangan__admin=request.user)
    lapangan_id = jadwal.lapangan.id
    jadwal.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'Jadwal berhasil dihapus!'})
    
    messages.success(request, 'Jadwal berhasil dihapus!')
    return redirect('admin_lapangan:jadwal_list', lapangan_id=lapangan_id)

########## numpang
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib import messages
from .models import UserProfile
from django.db import transaction

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        fullname = request.POST.get('fullname')
        location = request.POST.get('location', '')
        role = request.POST.get('role', 'user')
        profile_picture = request.FILES.get('profile_picture')
        
        # Validation
        if not username or not password or not fullname:
            messages.error(request, 'Username, password, dan nama lengkap wajib diisi!')
            return render(request, 'authentication_user/register.html')
        
        if password != password_confirm:
            messages.error(request, 'Password dan konfirmasi password tidak cocok!')
            return render(request, 'authentication_user/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username sudah digunakan!')
            return render(request, 'authentication_user/register.html')
        
        # Validate role
        if role not in ['user', 'admin']:
            messages.error(request, 'Role tidak valid!')
            return render(request, 'authentication_user/register.html')
        
        try:
            # Use transaction to ensure both User and UserProfile are created together
            with transaction.atomic():
                # Create User
                user = User.objects.create_user(
                    username=username,
                    password=password
                )
                
                # Create UserProfile
                user_profile = UserProfile.objects.create(
                    user=user,
                    fullname=fullname,
                    role=role,
                    location=location if location else None,
                    profile_picture=profile_picture if profile_picture else None
                )
            
            messages.success(request, 'Registrasi berhasil! Silakan login.')
            return redirect('authentication_user:login')
            
        except Exception as e:
            messages.error(request, f'Terjadi kesalahan: {str(e)}')
            return render(request, 'authentication_user/register.html')
    
    return render(request, 'authentication_user/register.html')


def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if not username or not password:
            messages.error(request, 'Username dan password wajib diisi!')
            return render(request, 'authentication_user/login.html')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            auth_login(request, user)
            
            # Check if user has profile
            if hasattr(user, 'profile'):
                messages.success(request, f'Selamat datang, {user.profile.fullname}!')
                
                # Redirect based on role (admin)
                if user.profile.role == 'admin':
                    return redirect('admin:index')  # Redirect to admin panel
                else:
                    return redirect('homepage')  # Redirect to homepage
            else: 
                messages.success(request, f'Selamat datang, {user.username}!')
                return redirect('homepage')
        else:
            messages.error(request, 'Username atau password salah!')
            return render(request, 'authentication_user/login.html')
    
    return render(request, 'authentication_user/login.html')