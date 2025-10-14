from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .models import Booking
#dummy
from lapangan.models import Lapangan, Jadwal

def make_booking(request):
    if request.method == 'POST':
        lapangan_id = request.POST.get('lapangan_id')
        jadwal_ids = request.POST.getlist('jadwal_id')  # Expecting a list of jadwal IDs

        lapangan = get_object_or_404(Lapangan, id=lapangan_id)
        jadwals = Jadwal.objects.filter(id__in=jadwal_ids, isbooked=False)

        if not jadwals.exists():
            messages.error(request, "Selected schedules are already booked or invalid.")
            return redirect('lapangan_detail', lapangan_id=lapangan_id)

        booking = Booking.objects.create(
            lapangan_id=lapangan,
            user_id=request.user,
            status_book='pending'
        )
        booking.jadwal.set(jadwals)
        booking.save()

        # Mark jadwals as booked
        jadwals.update(isbooked=True )

        messages.success(request, "Booking created successfully!")
        return redirect('booking_detail', booking_id=booking.id)

    return redirect('lapangan_list')