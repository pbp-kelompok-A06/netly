from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
<<<<<<< HEAD
=======
from django.db.models import Q
>>>>>>> b0e7c14c596c2fc59cab014026bfe81c955e47e5
from .models import Lapangan, JadwalLapangan
from .forms import LapanganForm, JadwalLapanganForm
from django.contrib.auth.decorators import login_required

def is_admin(user):
    return hasattr(user, 'profile') and user.profile.role == 'admin'

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('authentication_user:login')
        if not is_admin(request.user):
            return HttpResponseForbidden("You don't have permission to access this page.")
        return view_func(request, *args, **kwargs)
    return wrapper

# Dashboard
<<<<<<< HEAD
@admin_required
def admin_dashboard(request):
    recent_lapangan = Lapangan.objects.filter(admin=request.user)[:5]
=======
@login_required(login_url='/login/')
@admin_required
def admin_dashboard(request):
    recent_lapangan = Lapangan.objects.filter(
        admin_lapangan=request.user.profile
    ).order_by('-created_at')[:5]
>>>>>>> b0e7c14c596c2fc59cab014026bfe81c955e47e5
    
    context = {
        'recent_lapangan': recent_lapangan,
    }
<<<<<<< HEAD
    return render(request, 'admin_lapangan/dashboard.html', context)
=======
    return render(request, 'dashboard.html', context)
>>>>>>> b0e7c14c596c2fc59cab014026bfe81c955e47e5

# Lapangan CRUD
@login_required(login_url='/login/')
@admin_required
def show_lapangan_list(request):
<<<<<<< HEAD
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
=======
    search_query = request.GET.get('search', '').strip()
    
    # Base queryset - only show lapangan owned by current admin
    lapangan_list = Lapangan.objects.filter(
        admin_lapangan=request.user.profile
    )
    
    # FIXED: Apply search filter properly using Q objects
    if search_query:
        lapangan_list = lapangan_list.filter(
            Q(name__icontains=search_query) | Q(location__icontains=search_query)
        )
    
    # Order by creation date
    lapangan_list = lapangan_list.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(lapangan_list, 10)
    page_number = request.GET.get('page')
    lapangans = paginator.get_page(page_number)
    
    context = {
        'lapangans': lapangans,
        'search_query': search_query,
    }
    return render(request, 'lapangan_list.html', context)

@login_required(login_url='/login/')
@admin_required
def lapangan_detail(request, pk):
    lapangan = get_object_or_404(
        Lapangan, 
        pk=pk, 
        admin_lapangan=request.user.profile
    )
    
    # Ambil jadwal terkait
    jadwals = lapangan.jadwal.all().order_by('tanggal', 'start_main')[:10]  
    
    context = {
        'lapangan': lapangan,
        'jadwals': jadwals,
    }
    return render(request, 'lapangan_detail.html', context)
>>>>>>> b0e7c14c596c2fc59cab014026bfe81c955e47e5

@login_required(login_url='/login/')
@admin_required
def create_lapangan_ajax(request):
    if request.method == 'POST':
<<<<<<< HEAD
        form = LapanganForm(request.POST, request.FILES)
        if form.is_valid():
            lapangan = form.save(commit=False)
            lapangan.admin = request.user
=======
        form = LapanganForm(request.POST)  
        if form.is_valid():
            lapangan = form.save(commit=False)
            lapangan.admin_lapangan = request.user.profile  
>>>>>>> b0e7c14c596c2fc59cab014026bfe81c955e47e5
            lapangan.save()
            return JsonResponse({
                'status': 'success',
                'message': 'Lapangan berhasil ditambahkan!',
                'data': {
                    'id': str(lapangan.id),
                    'name': lapangan.name,
                    'location': lapangan.location
                }
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Validasi gagal',
                'errors': form.errors
            }, status=400)
<<<<<<< HEAD
    else:
        form = LapanganForm()
    
    return render(request, 'admin_lapangan/lapangan_form.html', {'form': form, 'action': 'Create'})
=======
    
    return JsonResponse({
        'status': 'error',
        'message': 'Method not allowed'
    }, status=405)
>>>>>>> b0e7c14c596c2fc59cab014026bfe81c955e47e5

@login_required(login_url='/login/')
@admin_required
def get_lapangan_json(request, pk):
    try:
<<<<<<< HEAD
        lapangan = Lapangan.objects.get(pk=pk, admin=request.user)
=======
        lapangan = Lapangan.objects.get(
            pk=pk, 
            admin_lapangan=request.user.profile
        )
>>>>>>> b0e7c14c596c2fc59cab014026bfe81c955e47e5
        data = {
            'id': str(lapangan.id),
            'name': lapangan.name,
            'location': lapangan.location,
            'description': lapangan.description,
            'price': str(lapangan.price),
<<<<<<< HEAD
            'image': lapangan.image.url if lapangan.image else ''
        }
        return JsonResponse({'status': 'success', 'data': data})
    except Lapangan.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Lapangan tidak ditemukan'}, status=404)
=======
            'image': lapangan.image or ''  # CHANGED: direct value, no .url
        }
        return JsonResponse({'status': 'success', 'data': data})
    except Lapangan.DoesNotExist:
        return JsonResponse({
            'status': 'error', 
            'message': 'Lapangan tidak ditemukan'
        }, status=404)
>>>>>>> b0e7c14c596c2fc59cab014026bfe81c955e47e5

@login_required(login_url='/login/')
@admin_required
def edit_lapangan_ajax(request, pk):
<<<<<<< HEAD
    try:
        lapangan = Lapangan.objects.get(pk=pk, admin=request.user)
        form = LapanganForm(request.POST, request.FILES, instance=lapangan)
=======
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'message': 'Method not allowed'
        }, status=405)
    
    try:
        lapangan = Lapangan.objects.get(pk=pk, admin_lapangan=request.user.profile)
        form = LapanganForm(request.POST, instance=lapangan)  # REMOVED: request.FILES
>>>>>>> b0e7c14c596c2fc59cab014026bfe81c955e47e5
        
        if form.is_valid():
            form.save()
            return JsonResponse({
                'status': 'success',
                'message': 'Lapangan berhasil diperbarui!'
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Validasi gagal',
                'errors': form.errors
            }, status=400)
    except Lapangan.DoesNotExist:
<<<<<<< HEAD
        return JsonResponse({'status': 'error', 'message': 'Lapangan tidak ditemukan'}, status=404)
=======
        return JsonResponse({
            'status': 'error', 
            'message': 'Lapangan tidak ditemukan'
        }, status=404)
>>>>>>> b0e7c14c596c2fc59cab014026bfe81c955e47e5

@login_required(login_url='/login/')
@admin_required
@require_http_methods(["POST", "DELETE"])
def delete_lapangan_ajax(request, pk):
    try:
<<<<<<< HEAD
        lapangan = Lapangan.objects.get(pk=pk, admin=request.user)
=======
        lapangan = Lapangan.objects.get(
            pk=pk, 
            admin_lapangan=request.user.profile
        )
>>>>>>> b0e7c14c596c2fc59cab014026bfe81c955e47e5
        lapangan_name = lapangan.name
        lapangan.delete()
        return JsonResponse({
            'status': 'success',
            'message': f'Lapangan "{lapangan_name}" berhasil dihapus!'
        })
    except Lapangan.DoesNotExist:
<<<<<<< HEAD
        return JsonResponse({'status': 'error', 'message': 'Lapangan tidak ditemukan'}, status=404)
=======
        return JsonResponse({
            'status': 'error', 
            'message': 'Lapangan tidak ditemukan'
        }, status=404)
>>>>>>> b0e7c14c596c2fc59cab014026bfe81c955e47e5

# Jadwal CRUD
@login_required(login_url='/login/')
@admin_required
def show_jadwal_list(request, lapangan_id):
<<<<<<< HEAD
    lapangan = get_object_or_404(Lapangan, id=lapangan_id, admin=request.user)
    jadwal = lapangan.jadwal.all().order_by('tanggal', 'start_main')
    
    context = {
        'lapangan': lapangan,
        'jadwal': jadwal,
    }
    return render(request, 'admin_lapangan/jadwal_list.html', context)

@admin_required
def create_jadwal_ajax(request, lapangan_id):
    try:
        lapangan = Lapangan.objects.get(pk=lapangan_id, admin=request.user)
=======
    lapangan = get_object_or_404(
        Lapangan, 
        id=lapangan_id, 
        admin_lapangan=request.user.profile
    )
    jadwals = lapangan.jadwal.all().order_by('tanggal', 'start_main')
    
    context = {
        'lapangan': lapangan,
        'jadwals': jadwals,
    }
    return render(request, 'jadwal_list.html', context)

@login_required(login_url='/login/')
@admin_required
def create_jadwal_ajax(request, lapangan_id):
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'message': 'Method not allowed'
        }, status=405)
    
    try:
        lapangan = Lapangan.objects.get(
            pk=lapangan_id, 
            admin_lapangan=request.user.profile
        )
>>>>>>> b0e7c14c596c2fc59cab014026bfe81c955e47e5
        form = JadwalLapanganForm(request.POST)
        
        if form.is_valid():
            jadwal = form.save(commit=False)
            jadwal.lapangan = lapangan
            jadwal.save()
            return JsonResponse({
                'status': 'success',
                'message': 'Jadwal berhasil ditambahkan!'
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Validasi gagal',
                'errors': form.errors
            }, status=400)
    except Lapangan.DoesNotExist:
<<<<<<< HEAD
        return JsonResponse({'status': 'error', 'message': 'Lapangan tidak ditemukan'}, status=404)

@admin_required
def edit_jadwal_ajax(request, pk):
    try:
        jadwal = JadwalLapangan.objects.get(pk=pk, lapangan__admin=request.user)
=======
        return JsonResponse({
            'status': 'error', 
            'message': 'Lapangan tidak ditemukan'
        }, status=404)

@login_required(login_url='/login/')
@admin_required
def get_jadwal_json(request, pk):
    try:
        jadwal = JadwalLapangan.objects.get(
            pk=pk, 
            lapangan__admin_lapangan=request.user.profile
        )
        data = {
            'id': str(jadwal.id),
            'tanggal': jadwal.tanggal.strftime('%Y-%m-%d'),
            'start_main': jadwal.start_main.strftime('%H:%M'),
            'end_main': jadwal.end_main.strftime('%H:%M'),
            'is_available': jadwal.is_available
        }
        return JsonResponse({'status': 'success', 'data': data})
    except JadwalLapangan.DoesNotExist:
        return JsonResponse({
            'status': 'error', 
            'message': 'Jadwal tidak ditemukan'
        }, status=404)

@login_required(login_url='/login/')
@admin_required
def edit_jadwal_ajax(request, pk):
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'message': 'Method not allowed'
        }, status=405)
    
    try:
        jadwal = JadwalLapangan.objects.get(
            pk=pk, 
            lapangan__admin_lapangan=request.user.profile
        )
>>>>>>> b0e7c14c596c2fc59cab014026bfe81c955e47e5
        form = JadwalLapanganForm(request.POST, instance=jadwal)
        
        if form.is_valid():
            form.save()
            return JsonResponse({
                'status': 'success',
                'message': 'Jadwal berhasil diperbarui!'
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Validasi gagal',
                'errors': form.errors
            }, status=400)
    except JadwalLapangan.DoesNotExist:
<<<<<<< HEAD
        return JsonResponse({'status': 'error', 'message': 'Jadwal tidak ditemukan'}, status=404)

=======
        return JsonResponse({
            'status': 'error', 
            'message': 'Jadwal tidak ditemukan'
        }, status=404)

@login_required(login_url='/login/')
>>>>>>> b0e7c14c596c2fc59cab014026bfe81c955e47e5
@admin_required
@require_http_methods(["POST", "DELETE"])
def delete_jadwal_ajax(request, pk):
    try:
<<<<<<< HEAD
        jadwal = JadwalLapangan.objects.get(pk=pk, lapangan__admin=request.user)
=======
        jadwal = JadwalLapangan.objects.get(
            pk=pk, 
            lapangan__admin_lapangan=request.user.profile
        )
>>>>>>> b0e7c14c596c2fc59cab014026bfe81c955e47e5
        jadwal.delete()
        return JsonResponse({
            'status': 'success',
            'message': 'Jadwal berhasil dihapus!'
        })
    except JadwalLapangan.DoesNotExist:
<<<<<<< HEAD
        return JsonResponse({'status': 'error', 'message': 'Jadwal tidak ditemukan'}, status=404)

@admin_required
def get_jadwal_json(request, pk):
    try:
        jadwal = JadwalLapangan.objects.get(pk=pk, lapangan__admin=request.user)
        data = {
            'id': str(jadwal.id),
            'tanggal': jadwal.tanggal.strftime('%Y-%m-%d'),
            'start_main': jadwal.start_main.strftime('%H:%M'),
            'end_main': jadwal.end_main.strftime('%H:%M'),
            'is_available': jadwal.is_available
        }
        return JsonResponse({'status': 'success', 'data': data})
    except JadwalLapangan.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Jadwal tidak ditemukan'}, status=404)
=======
        return JsonResponse({
            'status': 'error', 
            'message': 'Jadwal tidak ditemukan'
        }, status=404)
    

@login_required(login_url='/login/')
@admin_required
def fetch_lapangan_list_ajax(request):
    search_query = request.GET.get('search', '').strip()
    
    lapangan_list = Lapangan.objects.filter(
        admin_lapangan=request.user.profile
    )
    
    if search_query:
        lapangan_list = lapangan_list.filter(
            Q(name__icontains=search_query) | Q(location__icontains=search_query)
        )
    
    lapangan_list = lapangan_list.order_by('-created_at')
    
    data = []
    for lapangan in lapangan_list:
        data.append({
            'id': str(lapangan.id),
            'name': lapangan.name,
            'location': lapangan.location,
            'price': float(lapangan.price),
            'image': lapangan.image or '',
        })
    
    return JsonResponse({'status': 'success', 'data': data})

@login_required(login_url='/login/')
@admin_required
def fetch_jadwal_list_ajax(request, lapangan_id):
    try:
        lapangan = Lapangan.objects.get(
            pk=lapangan_id, 
            admin_lapangan=request.user.profile
        )
        jadwals = lapangan.jadwal.all().order_by('tanggal', 'start_main')
        
        data = []
        for jadwal in jadwals:
            data.append({
                'id': str(jadwal.id),
                'tanggal': jadwal.tanggal.strftime('%Y-%m-%d'),
                'start_main': jadwal.start_main.strftime('%H:%M'),
                'end_main': jadwal.end_main.strftime('%H:%M'),
                'is_available': jadwal.is_available,
            })
        
        return JsonResponse({'status': 'success', 'data': data})
    except Lapangan.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Lapangan tidak ditemukan'
        }, status=404)
>>>>>>> b0e7c14c596c2fc59cab014026bfe81c955e47e5
