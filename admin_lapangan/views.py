from datetime import datetime, time
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
from django.views.decorators.csrf import csrf_exempt
from django.utils.html import strip_tags
from django.views.decorators.http import require_POST
from functools import wraps

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
            'image': lapangan.image or ''  
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
    
@csrf_exempt
@admin_required
def get_all_lapangan_json(request):
    search_query = request.GET.get('search', '').strip()
    
    lapangan_list = Lapangan.objects.filter(
        admin_lapangan=request.user.profile
    )
    
    # Apply search filter
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
            'description': lapangan.description,
            'price': float(lapangan.price),
            'image': lapangan.image or '',
            'admin_name': lapangan.admin_lapangan.fullname,
        })
    
    return JsonResponse({'status': 'success', 'data': data})

@login_required(login_url='/login/')
@admin_required
def get_lapangan_detail_json(request, pk):
    try:
        # Build query based on user role
        if hasattr(request.user, 'profile') and request.user.profile.role == 'admin':
            # Admin: hanya bisa lihat lapangan milik mereka
            lapangan = Lapangan.objects.get(
                pk=pk,
                admin_lapangan=request.user.profile
            )
        
        data = {
            'id': str(lapangan.id),
            'name': lapangan.name,
            'location': lapangan.location,
            'description': lapangan.description,
            'price': float(lapangan.price),
            'image': lapangan.image or '',
            'admin_name': lapangan.admin_lapangan.fullname if lapangan.admin_lapangan else 'Unknown',
            'created_at': lapangan.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': lapangan.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        }
        return JsonResponse({'status': 'success', 'data': data})
    except Lapangan.DoesNotExist:
        return JsonResponse({
            'status': 'error', 
            'message': 'Lapangan tidak ditemukan atau Anda tidak memiliki akses'
        }, status=404)

@require_POST
@csrf_exempt
@admin_required
def create_lapangan_flutter(request):
    try:
        # Check authentication
        if not request.user.is_authenticated:
            return JsonResponse({
                "status": "error",
                "message": "Authentication required"
            }, status=401)
        
        # Check if user has profile and is admin
        if not hasattr(request.user, 'profile'):
            return JsonResponse({
                "status": "error",
                "message": "User profile not found"
            }, status=403)
        
        if request.user.profile.role != 'admin':
            return JsonResponse({
                "status": "error",
                "message": "Only admin can create lapangan"
            }, status=403)
        
        # Get data from POST
        name = strip_tags(request.POST.get("name", ""))
        location = strip_tags(request.POST.get("location", ""))
        description = strip_tags(request.POST.get("description", ""))
        price = request.POST.get("price", 0)
        image = request.POST.get("image", "")

        # Validate required fields
        if not name or not location:
            return JsonResponse({
                "status": "error",
                "message": "Name dan location wajib diisi."
            }, status=400)

        # Validate price
        try:
            price_decimal = Decimal(price)
            if price_decimal < 0:
                return JsonResponse({
                    "status": "error",
                    "message": "Harga tidak boleh negatif."
                }, status=400)
        except (ValueError, TypeError):
            return JsonResponse({
                "status": "error",
                "message": "Harga harus berupa angka."
            }, status=400)

        # Create Lapangan - assign to current logged-in admin
        new_lapangan = Lapangan(
            name=name,
            location=location,
            description=description,
            price=price_decimal,
            image=image if image else None,
            admin_lapangan=request.user.profile 
        )
        new_lapangan.save()

        return JsonResponse({
            "status": "success",
            "message": "Lapangan berhasil dibuat!",
            "data": {
                "id": str(new_lapangan.id),
                "name": new_lapangan.name,
                "location": new_lapangan.location,
                "description": new_lapangan.description,
                "price": int(new_lapangan.price),
                "image": new_lapangan.image if new_lapangan.image else "",
                "admin_name": request.user.profile.fullname
            }
        }, status=200)

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": f"Terjadi kesalahan: {str(e)}"
        }, status=500)

@csrf_exempt
@admin_required
@require_POST
def edit_lapangan_flutter(request, lapangan_id):
    try:
        # Check authentication
        if not request.user.is_authenticated:
            return JsonResponse({
                'status': 'error',
                'message': 'Authentication required'
            }, status=401)
        
        # Get lapangan - must belong to current admin
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'admin':
            return JsonResponse({
                'status': 'error',
                'message': 'Only admin can edit lapangan'
            }, status=403)
        
        # Get lapangan and verify ownership
        try:
            lapangan = Lapangan.objects.get(
                id=lapangan_id,
                admin_lapangan=request.user.profile  
            )
        except Lapangan.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Lapangan tidak ditemukan atau Anda tidak memiliki akses'
            }, status=404)

        # Get data from POST
        name = request.POST.get('name')
        location = request.POST.get('location')
        description = request.POST.get('description')
        price = request.POST.get('price')
        image = request.POST.get('image', '')

        # Validate required fields
        if not all([name, location, description, price]):
            return JsonResponse({
                'status': 'error',
                'message': 'Semua field wajib diisi'
            }, status=400)

        # Update lapangan
        lapangan.name = name
        lapangan.location = location
        lapangan.description = description
        lapangan.price = int(price)
        lapangan.image = image
        lapangan.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Lapangan berhasil diperbarui!',
            'data': {
                'id': str(lapangan.id),
                'name': lapangan.name,
                'location': lapangan.location,
                'description': lapangan.description,
                'price': lapangan.price,
                'image': lapangan.image,
                'admin_name': lapangan.admin_lapangan.fullname
            }
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Terjadi kesalahan: {str(e)}'
        }, status=500)

@csrf_exempt
@admin_required
@require_POST
def delete_lapangan_flutter(request, lapangan_id):
    try:
        # Check authentication
        if not request.user.is_authenticated:
            return JsonResponse({
                'status': 'error',
                'message': 'Authentication required'
            }, status=401)
        
        # Check admin role
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'admin':
            return JsonResponse({
                'status': 'error',
                'message': 'Only admin can delete lapangan'
            }, status=403)
        
        # Get lapangan and verify ownership
        try:
            lapangan = Lapangan.objects.get(
                id=lapangan_id,
                admin_lapangan=request.user.profile  
            )
        except Lapangan.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Lapangan tidak ditemukan atau Anda tidak memiliki akses'
            }, status=404)

        # Store name before delete
        lapangan_name = lapangan.name

        # Delete lapangan
        lapangan.delete()

        return JsonResponse({
            'status': 'success',
            'message': f'Lapangan "{lapangan_name}" berhasil dihapus!'
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Terjadi kesalahan: {str(e)}'
        }, status=500)

@admin_required    
def get_jadwal_by_lapangan(request, lapangan_id):
    try:
        # Check if lapangan exists
        lapangan = Lapangan.objects.get(id=lapangan_id)
        
        # Get date filter from query params
        filter_date = request.GET.get('date')
        
        jadwal_queryset = JadwalLapangan.objects.filter(
            lapangan_id=lapangan
        ).order_by('tanggal', 'start_main')
        
        # Apply date filter if provided
        if filter_date:
            try:
                date_obj = datetime.strptime(filter_date, '%Y-%m-%d').date()
                jadwal_queryset = jadwal_queryset.filter(tanggal=date_obj)
            except ValueError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Format tanggal tidak valid. Gunakan YYYY-MM-DD'
                }, status=400)
        
        # Serialize data
        jadwal_list = []
        for jadwal in jadwal_queryset:
            jadwal_list.append({
                'id': str(jadwal.id),
                'tanggal': jadwal.tanggal.strftime('%Y-%m-%d'),
                'start_main': jadwal.start_main.strftime('%H:%M'),
                'end_main': jadwal.end_main.strftime('%H:%M'),
                'is_available': jadwal.is_available,
            })
        
        return JsonResponse({
            'status': 'success',
            'data': jadwal_list
        })
    
    except Lapangan.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Lapangan tidak ditemukan'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Terjadi kesalahan: {str(e)}'
        }, status=500)

@admin_required
def get_jadwal_detail(request, jadwal_id):
    try:
        jadwal = JadwalLapangan.objects.get(id=jadwal_id)
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'id': str(jadwal.id),
                'tanggal': jadwal.tanggal.strftime('%Y-%m-%d'),
                'start_main': jadwal.start_main.strftime('%H:%M'),
                'end_main': jadwal.end_main.strftime('%H:%M'),
                'is_available': jadwal.is_available,
                'lapangan_id': str(jadwal.lapangan_id.id),
                'lapangan_name': jadwal.lapangan_id.name,
            }
        })
    
    except JadwalLapangan.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Jadwal tidak ditemukan'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Terjadi kesalahan: {str(e)}'
        }, status=500)

@csrf_exempt
@admin_required
def create_jadwal_flutter(request):
    try:
        # Get data from POST
        lapangan_id = request.POST.get('lapangan_id')
        tanggal_str = request.POST.get('tanggal')
        start_main_str = request.POST.get('start_main')
        end_main_str = request.POST.get('end_main')
        
        # Validate required fields
        if not all([lapangan_id, tanggal_str, start_main_str, end_main_str]):
            return JsonResponse({
                'status': 'error',
                'message': 'Semua field wajib diisi'
            }, status=400)
        
        # Get lapangan
        try:
            lapangan = Lapangan.objects.get(id=lapangan_id)
        except Lapangan.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Lapangan tidak ditemukan'
            }, status=404)
        
        # Parse date and time
        try:
            tanggal = datetime.strptime(tanggal_str, '%Y-%m-%d').date()
            start_main = datetime.strptime(start_main_str, '%H:%M').time()
            end_main = datetime.strptime(end_main_str, '%H:%M').time()
        except ValueError as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Format tanggal/waktu tidak valid: {str(e)}'
            }, status=400)
        
        # Validate date is not in the past
        from datetime import date as date_today
        if tanggal < date_today.today():
            return JsonResponse({
                'status': 'error',
                'message': 'Tanggal tidak boleh di masa lalu'
            }, status=400)
        
        # Validate start time < end time
        if start_main >= end_main:
            return JsonResponse({
                'status': 'error',
                'message': 'Waktu mulai harus lebih awal dari waktu selesai'
            }, status=400)
        
        # Check for overlapping schedules
        overlapping = JadwalLapangan.objects.filter(
            lapangan_id=lapangan,
            tanggal=tanggal,
            start_main__lt=end_main,
            end_main__gt=start_main
        ).exists()
        
        if overlapping:
            return JsonResponse({
                'status': 'error',
                'message': 'Jadwal bertabrakan dengan jadwal yang sudah ada'
            }, status=400)
        
        # Create jadwal
        jadwal = JadwalLapangan.objects.create(
            lapangan_id=lapangan_id,
            tanggal=tanggal,
            start_main=start_main,
            end_main=end_main,
            is_available=True
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Jadwal berhasil ditambahkan!',
            'data': {
                'id': str(jadwal.id),
                'tanggal': jadwal.tanggal.strftime('%Y-%m-%d'),
                'start_main': jadwal.start_main.strftime('%H:%M'),
                'end_main': jadwal.end_main.strftime('%H:%M'),
                'is_available': jadwal.is_available,
            }
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Terjadi kesalahan: {str(e)}'
        }, status=500)


@csrf_exempt
@admin_required
@require_POST
def edit_jadwal_flutter(request, jadwal_id):
    try:
        # Get jadwal
        jadwal = JadwalLapangan.objects.get(id=jadwal_id)
        
        # Get data from POST
        tanggal_str = request.POST.get('tanggal')
        start_main_str = request.POST.get('start_main')
        end_main_str = request.POST.get('end_main')
        is_available_str = request.POST.get('is_available')
        
        # Validate required fields
        if not all([tanggal_str, start_main_str, end_main_str]):
            return JsonResponse({
                'status': 'error',
                'message': 'Semua field wajib diisi'
            }, status=400)
        
        # Parse date and time
        try:
            tanggal = datetime.strptime(tanggal_str, '%Y-%m-%d').date()
            start_main = datetime.strptime(start_main_str, '%H:%M').time()
            end_main = datetime.strptime(end_main_str, '%H:%M').time()
        except ValueError as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Format tanggal/waktu tidak valid: {str(e)}'
            }, status=400)
        
        # Validate start time < end time
        if start_main >= end_main:
            return JsonResponse({
                'status': 'error',
                'message': 'Waktu mulai harus lebih awal dari waktu selesai'
            }, status=400)
        
        # Check for overlapping schedules (exclude current jadwal)
        overlapping = JadwalLapangan.objects.filter(
            lapangan_id=jadwal.lapangan_id,
            tanggal=tanggal,
            start_main__lt=end_main,
            end_main__gt=start_main
        ).exclude(id=jadwal_id).exists()
        
        if overlapping:
            return JsonResponse({
                'status': 'error',
                'message': 'Jadwal bertabrakan dengan jadwal yang sudah ada'
            }, status=400)
        
        # Update jadwal
        jadwal.tanggal = tanggal
        jadwal.start_main = start_main
        jadwal.end_main = end_main
        
        if is_available_str is not None:
            jadwal.is_available = is_available_str.lower() == 'true'
        
        jadwal.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Jadwal berhasil diperbarui!',
            'data': {
                'id': str(jadwal.id),
                'tanggal': jadwal.tanggal.strftime('%Y-%m-%d'),
                'start_main': jadwal.start_main.strftime('%H:%M'),
                'end_main': jadwal.end_main.strftime('%H:%M'),
                'is_available': jadwal.is_available,
            }
        })
    
    except JadwalLapangan.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Jadwal tidak ditemukan'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Terjadi kesalahan: {str(e)}'
        }, status=500)


@csrf_exempt
@admin_required
@require_POST
def delete_jadwal_flutter(request, jadwal_id):
    try:
        # Get jadwal
        jadwal = JadwalLapangan.objects.get(id=jadwal_id)
        
        # Store info before delete
        tanggal = jadwal.tanggal
        start = jadwal.start_main
        
        # Delete jadwal
        jadwal.delete()
        
        return JsonResponse({
            'status': 'success',
            'message': f'Jadwal {tanggal} ({start}) berhasil dihapus!'
        })
    
    except JadwalLapangan.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Jadwal tidak ditemukan'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Terjadi kesalahan: {str(e)}'
        }, status=500)
    
@csrf_exempt
@admin_required
@require_POST
def toggle_availability_flutter(request, jadwal_id):
    try:
        jadwal = JadwalLapangan.objects.get(id=jadwal_id)
        
        # Get is_available from POST
        is_available_str = request.POST.get('is_available', '').lower()
        
        if is_available_str not in ['true', 'false']:
            return JsonResponse({
                'status': 'error',
                'message': 'is_available harus true atau false'
            }, status=400)
        
        jadwal.is_available = is_available_str == 'true'
        jadwal.save()
        
        return JsonResponse({
            'status': 'success',
            'message': f'Jadwal berhasil diubah menjadi {"tersedia" if jadwal.is_available else "tidak tersedia"}!'
        })
    
    except JadwalLapangan.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Jadwal tidak ditemukan'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Terjadi kesalahan: {str(e)}'
        }, status=500)