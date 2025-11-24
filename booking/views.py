from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .models import Booking
from django.utils import timezone  
from datetime import timedelta
from admin_lapangan.models import Lapangan
from admin_lapangan.models import JadwalLapangan as Jadwal
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from datetime import datetime

def test(request):
    
    return render(request, 'booking_detail.html')

def show_create_booking(request, lapangan_id):
    
    today = timezone.now().date() 
    # Tentukan batas akhir (hari ini + 2 hari)
    limit_date = today + timedelta(days=2)
    # -----------------------------

    
    jadwals = Jadwal.objects.filter(
        lapangan_id=lapangan_id, 
        is_available=True,
        tanggal__gte=today,       # Filter 1: Tanggal >= hari ini
        tanggal__lte=limit_date     # Filter 2: Tanggal <= hari ini + 2 hari
    ).order_by('tanggal', 'start_main')
    context = {
        'lapangan': get_object_or_404(Lapangan, id=lapangan_id),
        'jadwals': jadwals
    }
    return render(request, 'create_book.html', context)

@csrf_exempt  # kalau belum handle CSRF token di JS, tapi idealnya pakai token ya
@login_required(login_url='authentication_user:login')
def create_booking(request):
    if request.method == 'POST':
        lapangan_id = request.POST.get('lapangan_id')
        jadwal_ids = request.POST.getlist('jadwal_id')

        lapangan = get_object_or_404(Lapangan, id=lapangan_id)
        jadwals = Jadwal.objects.filter(id__in=jadwal_ids, is_available=True)

        if not jadwals.exists():
            return JsonResponse({'success': False, 
                                 'message': 'Selected schedules are already booked or invalid.'}, 
                                status=400,
                                )
        
        #kalo berhasil
        booking = Booking.objects.create(
            lapangan_id=lapangan,
            user_id=request.user.profile,  # Asumsi ada relasi OneToOne antara User dan UserProfile
            status_book='pending'
        )
        booking.jadwal.set(jadwals)
        jadwals.update(is_available=False)
        payment_url = reverse('booking:booking_detail', kwargs={'booking_id': booking.id})

        return JsonResponse({
            'success': True,
            'message': 'Booking created successfully!',
            'booking_id': str(booking.id),
            'payment_url': payment_url
        })

    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)

def show_json_by_id(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    booking.is_expired()  # cek apakah booking sudah expired
    jadwal_list = list(booking.jadwal.values('tanggal', 'start_main', 'end_main', 'is_available'))
    data = {
        'id': str(booking.id),
        'lapangan': {
            'id': booking.lapangan_id.id,
            'name': booking.lapangan_id.name,
            'price': booking.lapangan_id.price,
        },
        'user': {
            'id': booking.user_id.id,
            'fullname': booking.user_id.fullname,
        },
        'created_at': booking.created_at,
        'status_book': booking.status_book,
        'total_price': booking.total_price(),
        'jadwal': jadwal_list,
    }
    # headers: { 'Accept': 'application/json' },
    return JsonResponse(data)



def show_json(request):
    if request.user.profile.role == 'admin':
        all_bookings = Booking.objects.filter(lapangan_id__admin_lapangan=request.user.profile).order_by('-created_at')
    else:
        # Ambil semua booking milik user yang sedang login
        all_bookings = Booking.objects.filter(user_id=request.user.profile.id).order_by('-created_at')

    data = []
    for booking in all_bookings:
        # Cek dan update status expired sebelum disajikan
        booking.is_expired() 

        # Ambil jadwal
        jadwal_list = list(booking.jadwal.values('tanggal', 'start_main', 'end_main'))

        # 2. Susun data untuk setiap booking
        data.append({
            'id': str(booking.id),
            'lapangan': {
                'id': str(booking.lapangan_id.id),
                'name': booking.lapangan_id.name, # Gunakan 'name' agar sesuai dengan JS di list page
                'price': booking.lapangan_id.price,
            },
            'user': {
                'id': str(booking.user_id.id),
                'fullname': booking.user_id.fullname,
            },
            
            'status_book': booking.status_book,
            'total_price': booking.total_price(),
            'jadwal': jadwal_list,
            'created_at': booking.created_at
        })

    
    return JsonResponse(data, safe=False)

@login_required(login_url='authentication_user:login')
def complete_booking(request, booking_id):
    # Ambil objek booking, pastikan hanya user yang bersangkutan yang bisa melakukannya
    try:
        booking = Booking.objects.get(id=booking_id, user_id=request.user.profile.id)
    except Booking.DoesNotExist:
        return JsonResponse({'message': 'Booking not found or not authorized'}, status=404)

    # Cek status sebelum update
    if booking.status_book == 'pending':
        booking.status_book = 'completed'
        booking.save()
        return JsonResponse({'message': 'Booking status updated to Completed', 'status': 'Completed'}, status=200)

    elif booking.status_book == 'failed' or booking.is_expired():
        return JsonResponse({'message': 'Booking has expired and cannot be completed'}, status=400)

    return JsonResponse({'message': f'Booking is already {booking.status_book}'}, status=200)

# flownya jadi dari create_booking di redirect ke booking_detail
def booking_detail(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    booking.is_expired()
    return render(request, 'booking_detail.html', {
        'booking_id': str(booking.id), # Kirim ID ke template agar JS bisa membacanya
        'lapangan_nama': booking.lapangan_id.name # Kirim data minimal untuk header
    })
    
# function untuk ngedirect ke booking_list


def show_booking_list(request):
    return render(request, 'booking_list.html')

# def show_json(request):
#     bookings = Booking.objects.filter(user_id=request.user.profile.id)
#     # Pastikan setiap booking dicek apakah sudah expired
#     for booking in bookings:
#         booking.is_expired()

#     data = []
#     for booking in bookings:
#         jadwal_list = list(booking.jadwal.values('tanggal', 'start_main', 'end_main', 'is_available'))
#         data.append({
#             'id': str(booking.id),
#             'lapangan': {
#                 'id': booking.lapangan_id.id,
#                 'name': booking.lapangan_id.name,
#                 'price': booking.lapangan_id.price,
#             },
#             'user': {
#                 'id': booking.user_id.id,

#             },
#             'created_at': booking.created_at,
#             'status_book': booking.status_book,
#             'total_price': booking.total_price(),
#             'jadwal': jadwal_list,
#         })
#     return JsonResponse(data, safe=False)
def delete_booking(request, booking_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)

    try:
        # 1. Ambil booking yang mau dihapus
        booking = Booking.objects.get(id=booking_id)
        now = timezone.now()
        
        # 3. Siapkan list untuk jadwal yang akan dibuka kembali
        jadwal_ids_to_reopen = []
        
        # 4. Cek setiap jadwal di dalam booking itu
        #    (Gunakan .all() sebelum booking dihapus)
        jadwals_in_booking = booking.jadwal.all()
        
        for jadwal in jadwals_in_booking:
            # Gabungkan tanggal dan jam selesai
            waktu_selesai = datetime.combine(jadwal.tanggal, jadwal.end_main)
            # Buat jadi 'aware' (sesuai zona waktu di settings.py)
            waktu_selesai_aware = timezone.make_aware(waktu_selesai)
            
            # 5. Cek: Apakah jadwal ini MASIH DI MASA DEPAN?
            if waktu_selesai_aware > now:
                # Jika ya (belum expired), masukkan ke list untuk dibuka
                jadwal_ids_to_reopen.append(jadwal.id)
            # Jika tidak (sudah expired), kita biarkan saja (is_available=False)

        # 6. Hapus booking-nya
        booking.delete()
        
        # 7. Buka kembali semua jadwal yang belum expired (jika ada)
        if jadwal_ids_to_reopen:
            Jadwal.objects.filter(id__in=jadwal_ids_to_reopen).update(is_available=True)
            
        return JsonResponse({
            'success': True, 
            'message': 'Booking berhasil dihapus dan jadwal yang belum lewat telah dibuka kembali.'
        }, status=200)
    
    except Booking.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Booking tidak ditemukan.'}, status=404)
    except Exception as e:
        # Tangkap error lain jika ada
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
def get_booking_data_flutter(request, lapangan_id):
    # 1. Ambil Logika Waktu (Sama seperti di show_create_booking)
    today = timezone.now().date() 
    limit_date = today + timedelta(days=2)
    
    # 2. Ambil Lapangan
    try:
        lapangan = Lapangan.objects.get(id=lapangan_id)
    except Lapangan.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Lapangan not found'}, status=404)

    # 3. Ambil Jadwal Available
    jadwals = Jadwal.objects.filter(
        lapangan_id=lapangan_id, 
        is_available=True,
        tanggal__gte=today,
        tanggal__lte=limit_date
    ).order_by('tanggal', 'start_main')

    # 4. Serialize Data Jadwal
    jadwal_data = []
    for j in jadwals:
        jadwal_data.append({
            "id": str(j.id),
            "tanggal": j.tanggal.strftime("%Y-%m-%d"),
            "start_main": j.start_main.strftime("%H:%M"),
            "end_main": j.end_main.strftime("%H:%M"),
            "is_available": j.is_available,
        })

    # 5. Return JSON
    return JsonResponse({
        "status": "success",
        "lapangan": {
            "id": str(lapangan.id),
            "name": lapangan.name,
            "price": lapangan.price, # Pastikan tipe datanya sesuai (float/int)
        },
        "jadwal_list": jadwal_data
    })