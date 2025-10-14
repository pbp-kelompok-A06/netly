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
            return JsonResponse({'success': False, 'message': 'Selected schedules are already booked or invalid.'}, status=400)

        
        #kalo berhasil
        booking = Booking.objects.create(
            lapangan_id=lapangan,
            user_id=request.user,
            status_book='pending'
        )
        booking.jadwal.set(jadwals)
        jadwals.update(isbooked=True)

        return JsonResponse({
            'success': True,
            'message': 'Booking created successfully!',
            'booking_id': str(booking.id)
        })

    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)
