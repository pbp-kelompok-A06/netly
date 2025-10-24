from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Lapangan, JadwalLapangan
from .forms import LapanganForm, JadwalLapanganForm
from django.contrib.auth.decorators import login_required
from decimal import Decimal
import os, json

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
@login_required(login_url='/login/')
@admin_required
def admin_dashboard(request):
    recent_lapangan = Lapangan.objects.filter(
        admin_lapangan=request.user.profile
    ).order_by('-created_at')[:5]
    
    context = {
        'recent_lapangan': recent_lapangan,
    }
    return render(request, 'dashboard.html', context)

# Lapangan CRUD
@login_required(login_url='/login/')
@admin_required
def show_lapangan_list(request):
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

@login_required(login_url='/login/')
@admin_required
def create_lapangan_ajax(request):
    if request.method == 'POST':
        form = LapanganForm(request.POST)  
        if form.is_valid():
            lapangan = form.save(commit=False)
            lapangan.admin_lapangan = request.user.profile  
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
    
    return JsonResponse({
        'status': 'error',
        'message': 'Method not allowed'
    }, status=405)

@login_required(login_url='/login/')
@admin_required
def get_lapangan_json(request, pk):
    try:
        lapangan = Lapangan.objects.get(
            pk=pk, 
            admin_lapangan=request.user.profile
        )
        data = {
            'id': str(lapangan.id),
            'name': lapangan.name,
            'location': lapangan.location,
            'description': lapangan.description,
            'price': str(lapangan.price),
            'image': lapangan.image or ''  # CHANGED: direct value, no .url
        }
        return JsonResponse({'status': 'success', 'data': data})
    except Lapangan.DoesNotExist:
        return JsonResponse({
            'status': 'error', 
            'message': 'Lapangan tidak ditemukan'
        }, status=404)

@login_required(login_url='/login/')
@admin_required
def edit_lapangan_ajax(request, pk):
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'message': 'Method not allowed'
        }, status=405)
    
    try:
        lapangan = Lapangan.objects.get(pk=pk, admin_lapangan=request.user.profile)
        form = LapanganForm(request.POST, instance=lapangan)  # REMOVED: request.FILES
        
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
        return JsonResponse({
            'status': 'error', 
            'message': 'Lapangan tidak ditemukan'
        }, status=404)

@login_required(login_url='/login/')
@admin_required
@require_http_methods(["POST", "DELETE"])
def delete_lapangan_ajax(request, pk):
    try:
        lapangan = Lapangan.objects.get(
            pk=pk, 
            admin_lapangan=request.user.profile
        )
        lapangan_name = lapangan.name
        lapangan.delete()
        return JsonResponse({
            'status': 'success',
            'message': f'Lapangan "{lapangan_name}" berhasil dihapus!'
        })
    except Lapangan.DoesNotExist:
        return JsonResponse({
            'status': 'error', 
            'message': 'Lapangan tidak ditemukan'
        }, status=404)

# Jadwal CRUD
@login_required(login_url='/login/')
@admin_required
def show_jadwal_list(request, lapangan_id):
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
        return JsonResponse({
            'status': 'error', 
            'message': 'Jadwal tidak ditemukan'
        }, status=404)

@login_required(login_url='/login/')
@admin_required
@require_http_methods(["POST", "DELETE"])
def delete_jadwal_ajax(request, pk):
    try:
        jadwal = JadwalLapangan.objects.get(
            pk=pk, 
            lapangan__admin_lapangan=request.user.profile
        )
        jadwal.delete()
        return JsonResponse({
            'status': 'success',
            'message': 'Jadwal berhasil dihapus!'
        })
    except JadwalLapangan.DoesNotExist:
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


@login_required(login_url='/login/')
@admin_required
def import_lapangan_data(request):
    
    try:
        json_file_path = os.path.join(os.path.dirname(__file__), 'badminton_final.json')
        
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        default_admin = request.user.profile
        
        created_count = 0
        skipped_count = 0
        error_count = 0
        errors = []
        

        for item in data:
            try:
                if Lapangan.objects.filter(name=item['nama_tempat']).exists():
                    skipped_count += 1
                    continue
                
                lapangan = Lapangan.objects.create(
                    admin_lapangan=default_admin,
                    name=item['nama_tempat'],
                    location=item['lokasi_tempat'],
                    description=f"Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.",
                    price=Decimal(item['harga_tempat']),
                    image=item['link_gambar']
                )
                
                created_count += 1
                
            except Exception as e:
                error_count += 1
                errors.append({
                    'nama_tempat': item.get('nama_tempat', 'Unknown'),
                    'error': str(e)
                })
        
        return JsonResponse({
            'success': True,
            'message': 'Import completed successfully',
            'stats': {
                'total_records': len(data),
                'created': created_count,
                'skipped': skipped_count,
                'errors': error_count
            },
            'errors': errors if errors else None
        })
        
    except FileNotFoundError:
        return JsonResponse({
            'success': False,
            'message': 'JSON file not found. Please ensure badminton_final.json is in the correct location.'
        })
    except json.JSONDecodeError as e:
        return JsonResponse({
            'success': False,
            'message': f'Invalid JSON format: {str(e)}'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Unexpected error: {str(e)}'
        })