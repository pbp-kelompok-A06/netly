from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .models import Booking
#dummy
from admin_lapangan.models import Lapangan
from admin_lapangan.models import JadwalLapangan as Jadwal

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

def test(request):
    
    return render(request, 'booking_detail.html')
@csrf_exempt  # kalau belum handle CSRF token di JS, tapi idealnya pakai token ya
# diuncomment kalo dah ada login
# @login_required
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
            user_id=request.user.profile.id,  # Asumsi ada relasi OneToOne antara User dan UserProfile
            status_book='pending'
        )
        booking.jadwal.update(jadwals)
        jadwals.update(is_available=False)
        #dummy
        payment_url = reverse('booking_detail', kwargs={'booking_id': booking.id})

        return JsonResponse({
            'success': True,
            'message': 'Booking created successfully!',
            'booking_id': str(booking.id),
            'payment_url': payment_url
        })

    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)

def show_json_by_id(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user_id=request.user.profile.id)
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
            'id': booking.user_id.profile.id,
            'fullname': booking.user_id.profile.fullname,
        },
        'created_at': booking.created_at,
        'status_book': booking.status_book,
        'total_price': booking.total_price(),
        'jadwal': jadwal_list,
    }
    # headers: { 'Accept': 'application/json' },
    return JsonResponse(data)


@login_required
def show_json(request):
    """
    Mengambil SEMUA booking untuk user yang sedang login dan mengembalikannya sebagai list JSON.
    Ini adalah view yang dibutuhkan oleh booking_list.html.
    """
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
                'harga': booking.lapangan_id.price,
            },
            
            'status_book': booking.status_book,
            'total_price': booking.total_price(),
            'jadwal': jadwal_list,
        })
        
    # 3. Kembalikan list JSON. safe=False diperlukan karena objek teratas adalah list.
    return JsonResponse(data, safe=False)

@login_required
def complete_booking(request, booking_id):
    # Ambil objek booking, pastikan hanya user yang bersangkutan yang bisa melakukannya
    try:
        booking = Booking.objects.get(id=booking_id, user_id=request.user_id.profile.id)
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
    # Pastikan booking_id valid dan user berhak melihatnya
    # Walaupun data detailnya diambil AJAX, kita tetap validasi ID dan user di sini
    booking = get_object_or_404(Booking, id=booking_id, user_id=request.user.profile.id)
    booking.is_expired()
    return render(request, 'booking_detail.html', {
        'booking_id': str(booking.id), # Kirim ID ke template agar JS bisa membacanya
        'lapangan_nama': booking.lapangan_id.name # Kirim data minimal untuk header
    })
    
# function untuk ngedirect ke booking_list
#EDLYNNN INI UNCOMMENT!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# @login_required
def show_booking_list(request):
    return render(request, 'booking_list.html')

def show_json(request):
    bookings = Booking.objects.filter(user_id=request.user.profile.id)
    # Pastikan setiap booking dicek apakah sudah expired
    for booking in bookings:
        booking.is_expired()

    data = []
    for booking in bookings:
        jadwal_list = list(booking.jadwal.values('tanggal', 'start_main', 'end_main', 'is_available'))
        data.append({
            'id': str(booking.id),
            'lapangan': {
                'id': booking.lapangan_id.id,
                'name': booking.lapangan_id.name,
                'price': booking.lapangan_id.price,
            },
            'user': {
                'id': booking.user_id.profile.id,

            },
            'created_at': booking.created_at,
            'status_book': booking.status_book,
            'total_price': booking.total_price(),
            'jadwal': jadwal_list,
        })
    return JsonResponse(data, safe=False)
