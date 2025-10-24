from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from datetime import datetime, date
from django.db.models import Q
from django.contrib.auth.decorators import login_required

# from modul lain
from admin_lapangan.models import Lapangan, JadwalLapangan
from authentication_user.models import UserProfile
from booking.models import Booking
from community.models import Forum

try:
    from event.models import Event
except Exception:
    Event = None

def _format_price(price):
    """Return string representation of price that JS/template can use safely."""
    try:
        # price mungkin Decimal -> tampilkan sebagai int jika .00, else as string
        if float(price).is_integer():
            return str(int(price))
        return str(price)
    except Exception:
        return str(price or "")


def _next_availability_status(lapangan):
    """
    Sederhanakan: kalau ada jadwal masa depan dengan is_available=True => 'Available'
    else 'Full' (atau kosong). Menggunakan model JadwalLapangan relation (related_name='jadwal').
    """
    try:
        today = date.today()
        next_jadwal = lapangan.jadwal.filter(tanggal__gte=today, is_available=True).order_by('tanggal', 'start_main').first()
        if next_jadwal:
            # bisa kembalikan tanggal juga, tapi sebelumnya template cuma menampilkan 'Available'
            return "Available"
        return "Full"
    except Exception:
        return ""
    
# Helper buat ubah object ke dict JSON
def serialize_lapangan(obj):
    return {
        "id": str(obj.id),
        "name": obj.name,
        "price": float(obj.price),
        "location": obj.location,
        "rating": getattr(obj, "rating", 4.5),  # fallback kalau belum ada kolom rating
        "status": "Available",
        "image": obj.image.url if getattr(obj, "image", None) else "",
        "description": obj.description,
    }

# homepage
@login_required(login_url='authentication_user:login')
def index(request):
    q = request.GET.get("q", "").strip()
    city = request.GET.get("city", "").strip()

    courts_qs = Lapangan.objects.all()

    # Jika user login dan dia admin -> tampilkan hanya lapangan miliknya
    if request.user.is_authenticated:
        profile = getattr(request.user, "profile", None)
        if profile and profile.role == "admin":
            courts_qs = courts_qs.filter(admin_lapangan=request.user)

    # Search & Filter
    if q:
        courts_qs = courts_qs.filter(Q(name__icontains=q) | Q(location__icontains=q))
    if city:
        courts_qs = courts_qs.filter(location__icontains=city)

    # Ambil semua lapangan
    court_list = [serialize_lapangan(c) for c in courts_qs]

    # Event
    event_list = []
    if Event:
        event_qs = Event.objects.all()
        if city:
            event_qs = event_qs.filter(location__icontains=city)
        event_list = [
            {
                "id": e.id,
                "name": e.name,
                "image": e.image.url if getattr(e, "image", None) else "",
                "description": e.description,
                "date": getattr(e, "date", ""),
                "location": e.location,
            }
            for e in event_qs[:5]
        ]

    # Jika user sedang search → sembunyikan carousel event
    if q:
        event_list = []

    context = {
        "court_list": court_list,
        "event_list": event_list,
        "search_query": request.GET,
        "user_profile": getattr(request.user, "profile", None)
        if request.user.is_authenticated
        else None,
    }
    return render(request, "homepage/index.html", context)

#  court detail page
def court_detail(request, court_id):
    """
    Menampilkan detail lapangan berdasarkan data nyata.
    """
    court = get_object_or_404(Lapangan, id=court_id)

    # buat tombol Book mengarah ke modul booking
    return render(request, "homepage/court_detail.html", {"court": court})

# booking redirect
def booking_placeholder(request, court_id=None):
    if not request.user.is_authenticated:
        return redirect("authentication_user:login")
    return redirect("booking:show_create_booking", lapangan_id=court_id)

# search & filter ajax
def search_courts_ajax(request):
    q = request.GET.get("q", "").strip()
    qs = Lapangan.objects.all()

    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(location__icontains=q))

    results = [serialize_lapangan(c) for c in qs[:20]]
    return JsonResponse({"results": results})


def filter_courts(request):
    location = request.GET.get("location", "").strip()
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    q = request.GET.get("q", "").strip()

    qs = Lapangan.objects.all()

    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(location__icontains=q))
    if location:
        qs = qs.filter(location__icontains=location)
    if min_price:
        qs = qs.filter(price__gte=min_price)
    if max_price:
        qs = qs.filter(price__lte=max_price)

    results = [serialize_lapangan(c) for c in qs]
    return JsonResponse({"results": results})


