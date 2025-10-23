from django.shortcuts import render, redirect
from datetime import datetime
from django.http import JsonResponse

# Dummy data untuk lapangan (lebih lengkap sesuai template)
COURT_LIST = [
    {
        "id": 1,
        "name": "Smash Arena",
        "price": 75000,
        "location": "Jakarta Selatan",
        "rating": 4.8,
        "status": "Available",
        "image": "https://cdn.myactivesg.com/Sports/Badminton/Facilities/ActiveSG-Badminton-Hall.jpg",
        "description": (
            "Smash Arena adalah GOR badminton modern dengan 4 lapangan berkarpet vinyl, "
            "penerangan LED terang, dan fasilitas ruang tunggu nyaman. "
            "Cocok untuk latihan harian maupun turnamen kecil."
        ),
    },
    {
        "id": 2,
        "name": "NetPro Court",
        "price": 65000,
        "location": "Bandung",
        "rating": 4.6,
        "status": "Available",
        "image": "https://img.olympics.com/images/image/private/t_s_16_9_g_auto/t_s_w960/f_auto/primary/kfsyzuaoipfhm4qonqci",
        "description": (
            "NetPro Court menyediakan 3 lapangan badminton indoor dengan sistem booking online. "
            "Setiap lapangan memiliki ventilasi baik dan area parkir luas."
        ),
    },
    {
        "id": 3,
        "name": "SkyBird Badminton",
        "price": 80000,
        "location": "Surabaya",
        "rating": 4.9,
        "status": "Available",
        "image": "https://blog.khelomore.com/wp-content/uploads/2022/02/MC44MjUxMzYwMCAxNDY4MjI1Njg3.jpeg",
        "description": (
            "SkyBird Badminton adalah fasilitas premium dengan 6 lapangan full AC dan karpet Yonex. "
            "Tersedia juga kafe dan ruang ganti modern untuk pemain."
        ),
    },
    {
        "id": 4,
        "name": "Ace Court",
        "price": 55000,
        "location": "Yogyakarta",
        "rating": 4.5,
        "status": "Available",
        "image": "https://cdn.mos.cms.futurecdn.net/T94A6VdniJsaCYaUFsCPWk.jpg",
        "description": (
            "Ace Court berlokasi strategis di pusat kota Yogyakarta dengan 5 lapangan indoor. "
            "Tersedia penyewaan raket dan layanan minuman ringan."
        ),
    },
    {
        "id": 5,
        "name": "Baseline Indoor",
        "price": 70000,
        "location": "Depok",
        "rating": 4.7,
        "status": "Available",
        "image": "https://www.activefitnessstore.com/media/catalog/product/cache/2/image/1800x/040ec09b1e35df139433887a97daa66f/b/a/badminton-court-flooring.jpg",
        "description": (
            "Baseline Indoor adalah GOR serbaguna dengan 4 lapangan badminton yang dilengkapi "
            "dengan sistem pencahayaan standar turnamen dan area lounge modern."
        ),
    },
]


# Dummy data untuk event (lebih lengkap)
EVENT_LIST = [
    {
        "id": 1,
        "name": "Netly Open 2025",
        "image": "https://images.unsplash.com/photo-1574629810360-7efbbe195018",
        "description": "Join the biggest amateur badminton tournament in Indonesia!",
        "date": "2025-11-20",
        "location": "Jakarta",
    },
    {
        "id": 2,
        "name": "Smash & Rally Festival",
        "image": "https://images.unsplash.com/photo-1600880292203-757bb62b4baf",
        "description": "Friendly matches, workshops, and live coaching.",
        "date": "2025-12-05",
        "location": "Bandung",
    },
    {
        "id": 3,
        "name": "Junior Badminton Cup",
        "image": "https://images.unsplash.com/photo-1574672280600-4f27d49aa0d0",
        "description": "Youth-exclusive championship!",
        "date": "2025-12-28",
        "location": "Surabaya",
    },
]

def index(request):
    """
    View untuk homepage.
    Menerima optional GET params: q, city, date, time
    dan memfilter dummy data supaya search/filters berfungsi pada level UI.
    """
    q = request.GET.get("q", "").strip().lower()
    city = request.GET.get("city", "").strip().lower()
    date = request.GET.get("date", "").strip() 
    time = request.GET.get("time", "").strip() 

    # Filter courts (copy original list)
    courts = COURT_LIST.copy()
    if q:
        courts = [c for c in courts if q in c["name"].lower() or q in c["location"].lower()]
    if city:
        courts = [c for c in courts if city in c["location"].lower()]

    # (Simple) Filter events by city/date
    events = EVENT_LIST.copy()
    if city:
        events = [e for e in events if city in e.get("location", "").lower()]
    if date:
        try:
            # validate date format; if invalid, ignore
            _ = datetime.strptime(date, "%Y-%m-%d")
            events = [e for e in events if e.get("date") == date]
        except ValueError:
            pass

    if q:
        events = []  # kosongin supaya section carousel gak ditampilkan

    # Context untuk template (sesuai fields yang template akses)
    context = {
        "court_list": courts,
        "event_list": events,
        # kembalikan param ke template agar form tetap terisi
        "search_query": request.GET,
    }
    return render(request, "homepage/index.html", context)

# =======================
#  COURT DETAIL PAGE
# =======================
def court_detail(request, court_id):
    """
    Menampilkan detail lapangan dan jadwal dummy.
    """
    court = next((c for c in COURT_LIST if c["id"] == int(court_id)), None)
    if not court:
        return redirect("homepage")

    return render(request, "homepage/court_detail.html", {"court": court})

# contoh view placeholder untuk booking (akan dipanggil ketika user meneruskan ke booking)
def booking_placeholder(request, court_id=None):
    """
    Placeholder: ketika user klik Book Now nanti diarahkan ke form booking nyata.
    Untuk sekarang, hanya menampilkan ringkasan dummy atau redirect.
    Tambahkan routing di urls.py: path('booking/<int:court_id>/', views.booking_placeholder, name='booking-placeholder')
    """
    # get court info by id (fallback ke first court)
    court = next((c for c in COURT_LIST if c["id"] == int(court_id)) , COURT_LIST[0] if COURT_LIST else None)
    if request.method == "POST":
        # nanti proses booking: validasi tanggal/waktu, simpan ke DB, redirect ke success page
        # sekarang redirect kembali ke homepage
        return redirect("homepage")
    return render(request, "homepage/booking_placeholder.html", {"court": court})

def search_courts_ajax(request):
    """
    Mengembalikan hasil search court dalam bentuk JSON (tanpa reload halaman).
    """
    q = request.GET.get("q", "").strip().lower()
    courts = [c for c in COURT_LIST if q in c["name"].lower() or q in c["location"].lower()] if q else []

    return JsonResponse({"results": courts})

def filter_courts(request):
    location = request.GET.get("location", "").lower()
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    query = request.GET.get("q", "").lower()

    filtered = []
    for c in COURT_LIST:
        if query and query not in c["name"].lower() and query not in c["location"].lower():
            continue
        if location and location not in c["location"].lower():
            continue
        if min_price and c["price"] < int(min_price):
            continue
        if max_price and c["price"] > int(max_price):
            continue
        filtered.append(c)

    return JsonResponse({"results": filtered})



