from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
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
@admin_required
def admin_dashboard(request):
    recent_lapangan = Lapangan.objects.filter(admin=request.user)[:5]
    
    context = {
        'recent_lapangan': recent_lapangan,
    }
    return render(request, 'admin_lapangan/dashboard.html', context)

# Lapangan CRUD
@login_required(login_url='/login/')
@admin_required
def show_lapangan_list(request):
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

@login_required(login_url='/login/')
@admin_required
def create_lapangan_ajax(request):
    if request.method == 'POST':
        form = LapanganForm(request.POST, request.FILES)
        if form.is_valid():
            lapangan = form.save(commit=False)
            lapangan.admin = request.user
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
    else:
        form = LapanganForm()
    
    return render(request, 'admin_lapangan/lapangan_form.html', {'form': form, 'action': 'Create'})

@login_required(login_url='/login/')
@admin_required
def get_lapangan_json(request, pk):
    try:
        lapangan = Lapangan.objects.get(pk=pk, admin=request.user)
        data = {
            'id': str(lapangan.id),
            'name': lapangan.name,
            'location': lapangan.location,
            'description': lapangan.description,
            'price': str(lapangan.price),
            'image': lapangan.image.url if lapangan.image else ''
        }
        return JsonResponse({'status': 'success', 'data': data})
    except Lapangan.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Lapangan tidak ditemukan'}, status=404)

@login_required(login_url='/login/')
@admin_required
def edit_lapangan_ajax(request, pk):
    try:
        lapangan = Lapangan.objects.get(pk=pk, admin=request.user)
        form = LapanganForm(request.POST, request.FILES, instance=lapangan)
        
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
        return JsonResponse({'status': 'error', 'message': 'Lapangan tidak ditemukan'}, status=404)

@login_required(login_url='/login/')
@admin_required
@require_http_methods(["POST", "DELETE"])
def delete_lapangan_ajax(request, pk):
    try:
        lapangan = Lapangan.objects.get(pk=pk, admin=request.user)
        lapangan_name = lapangan.name
        lapangan.delete()
        return JsonResponse({
            'status': 'success',
            'message': f'Lapangan "{lapangan_name}" berhasil dihapus!'
        })
    except Lapangan.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Lapangan tidak ditemukan'}, status=404)

# Jadwal CRUD
@login_required(login_url='/login/')
@admin_required
def show_jadwal_list(request, lapangan_id):
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
        return JsonResponse({'status': 'error', 'message': 'Lapangan tidak ditemukan'}, status=404)

@admin_required
def edit_jadwal_ajax(request, pk):
    try:
        jadwal = JadwalLapangan.objects.get(pk=pk, lapangan__admin=request.user)
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
        return JsonResponse({'status': 'error', 'message': 'Jadwal tidak ditemukan'}, status=404)

@admin_required
@require_http_methods(["POST", "DELETE"])
def delete_jadwal_ajax(request, pk):
    try:
        jadwal = JadwalLapangan.objects.get(pk=pk, lapangan__admin=request.user)
        jadwal.delete()
        return JsonResponse({
            'status': 'success',
            'message': 'Jadwal berhasil dihapus!'
        })
    except JadwalLapangan.DoesNotExist:
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