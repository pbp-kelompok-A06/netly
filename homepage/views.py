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
    
# Helper buat ubah object ke dict JSON
def serialize_lapangan(obj):
    return {
        "id": str(obj.id),
        "name": obj.name,
        "price": float(obj.price),
        "location": obj.location,
        "status": "Available",
        "image": obj.image or "",
        "description": obj.description,
    }

@login_required(login_url='authentication_user:login')
def index(request):
    profile = getattr(request.user, "profile", None)

    # Jika admin -> redirect atau render dashboard admin
    if profile and profile.role == "admin":
        # Ambil 5 lapangan terbaru milik admin
        profile = getattr(request.user, "profile", None)
        if profile and profile.role == "admin":
            recent_lapangan = Lapangan.objects.filter(admin_lapangan=profile).order_by('-created_at')[:5]

        context = {
            "recent_lapangan": recent_lapangan,
            "user_profile": profile,
        }
        return render(request, "dashboard.html", context)

    # USER BIASA -> homepage biasa
    q = request.GET.get("q", "").strip()
    city = request.GET.get("city", "").strip()
    courts_qs = Lapangan.objects.all()

    if q:
        courts_qs = courts_qs.filter(Q(name__icontains=q) | Q(location__icontains=q))
    if city:
        courts_qs = courts_qs.filter(location__icontains=city)

    court_list = [serialize_lapangan(c) for c in courts_qs]

    # Event
    event_list = []
    if Event:
        event_qs = Event.objects.all()
        if city:
            event_qs = event_qs.filter(location__icontains=city)

        # Event model punya field image_url -> pakai itu
        event_list = [
            {
                "id": e.id,
                "name": e.name,
                "image": e.image_url or "", 
                "description": e.description,
                "date": getattr(e, "start_date", ""),
                "location": e.location,
            }
            for e in event_qs[:5]
        ]

    # kalau user search, jangan tampilkan event
    if q:
        event_list = []

    context = {
        "court_list": court_list,
        "event_list": event_list,
        # kirim q sebagai string supaya template gampang nge-check
        "search_query": q,
        "user_profile": profile,
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

    # Search keyword
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(location__icontains=q))

    # Filter location jika ada
    if location:
        qs = qs.filter(location__icontains=location)

    # Filter price, pastikan tipe integer
    try:
        if min_price not in (None, ""):
            qs = qs.filter(price__gte=int(min_price))
        if max_price not in (None, ""):
            qs = qs.filter(price__lte=int(max_price))
    except ValueError:
        # Kalau input tidak valid, skip filter harga
        pass

    results = [serialize_lapangan(c) for c in qs]

    return JsonResponse({"results": results})



