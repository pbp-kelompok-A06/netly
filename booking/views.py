from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .models import Booking
#dummy
from lapangan.models import Lapangan, Jadwal

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

@csrf_exempt  # kalau belum handle CSRF token di JS, tapi idealnya pakai token ya
@login_required
def create_booking(request):
    if request.method == 'POST':
        lapangan_id = request.POST.get('lapangan_id')
        jadwal_ids = request.POST.getlist('jadwal_id')

        lapangan = get_object_or_404(Lapangan, id=lapangan_id)
        jadwals = Jadwal.objects.filter(id__in=jadwal_ids, isbooked=False)

        if not jadwals.exists():
            return JsonResponse({'success': False, 
                                 'message': 'Selected schedules are already booked or invalid.'}, 
                                status=400,
                                
                                )

        
        #kalo berhasil
        booking = Booking.objects.create(
            lapangan_id=lapangan,
            user_id=request.user,
            status_book='pending'
        )
        booking.jadwal.update(jadwals)
        jadwals.update(isbooked=True)
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
    booking = get_object_or_404(Booking, id=booking_id, user_id=request.user)
    booking.is_expired()  # cek apakah booking sudah expired
    jadwal_list = list(booking.jadwal.values('tanggal', 'waktu_mulai', 'waktu_selesai', 'isbooked'))
    data = {
        'id': str(booking.id),
        'lapangan': {
            'id': booking.lapangan_id.id,
            'nama': booking.lapangan_id.nama,
            'harga': booking.lapangan_id.harga,
        },
        'user': {
            'id': booking.user_id.id,
            'username': booking.user_id.username,
        },
        'created_at': booking.created_at,
        'status_book': booking.status_book,
        'total_price': booking.total_price(),
        'jadwal': jadwal_list,
    }
    # headers: { 'Accept': 'application/json' },
    return JsonResponse(data)

def pay_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user_id=request.user)
    if booking.is_expired():
        messages.error(request, 'Booking cannot be paid. Current status: {}'.format(booking.status_book))
        return redirect('booking_detail', booking_id=booking.id)

    # Simulate payment processing
    booking.status_book = 'completed'
    booking.save()
    messages.success(request, 'Payment successful! Your booking is now completed.')
    return redirect('booking_detail', booking_id=booking.id)

# flownya jadi dari create_booking di redirect ke booking_detail
def booking_detail(request, booking_id):
    # Pastikan booking_id valid dan user berhak melihatnya
    # Walaupun data detailnya diambil AJAX, kita tetap validasi ID dan user di sini
    booking = get_object_or_404(Booking, id=booking_id, user_id=request.user)
    booking.is_expired()
    return render(request, 'booking_detail.html', {
        'booking_id': str(booking.id), # Kirim ID ke template agar JS bisa membacanya
        'lapangan_nama': booking.lapangan_id.nama # Kirim data minimal untuk header
    })