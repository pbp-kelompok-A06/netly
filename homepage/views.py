import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import LapanganFavorit
from admin_lapangan.models import Lapangan

def serialize_lapangan(obj):
    """Mengubah object Lapangan jadi Dictionary untuk JSON"""
    image_url = ""
    if obj.image:
        if hasattr(obj.image, 'url'):
            image_url = obj.image.url
        else:
            image_url = str(obj.image)

    # FORMAT MANUAL RUPIAH (Pake Titik) untuk Tampilan Web
    formatted_price = f"{int(obj.price):,}".replace(",", ".")

    return {
        "id": str(obj.id),
        "name": obj.name,
        "price": float(obj.price), # FLUTTER baca ini (Angka)
        "formatted_price": formatted_price, # WEB baca ini (String Rp)
        "location": obj.location,
        "image": image_url, 
        "description": obj.description,
    }

def serialize_favorite_item(fav):
    image_url = ""
    if fav.lapangan.image:
        image_url = fav.lapangan.image.url if hasattr(fav.lapangan.image, 'url') else str(fav.lapangan.image)

    return {
        "id": str(fav.id),
        "user_id": fav.user.id,
        "label": fav.label, 
        "lapangan": {
            "id": str(fav.lapangan.id),
            "name": fav.lapangan.name,
            "location": fav.lapangan.location,
            "price": float(fav.lapangan.price),
            "image": image_url,
        }
    }

@login_required(login_url='authentication_user:login')
def index(request):
    """Homepage HTML (Wadah Awal)"""
    profile = getattr(request.user, "profile", None)
    
    # Jika admin -> redirect ke dashboard
    if profile and profile.role == "admin":
        recent_lapangan = Lapangan.objects.filter(admin_lapangan=profile).order_by('-created_at')[:5]
        context = {
            "recent_lapangan": recent_lapangan,
            "user_profile": profile,
        }
        return render(request, "dashboard.html", context)

    # Logic awal render HTML biasa (biar SEO bagus / load awal cepat)
    q = request.GET.get("q", "").strip()
    city = request.GET.get("city", "").strip()
    
    courts_qs = Lapangan.objects.all()
    if q: courts_qs = courts_qs.filter(Q(name__icontains=q) | Q(location__icontains=q))
    if city: courts_qs = courts_qs.filter(location__icontains=city)

    court_list = [serialize_lapangan(c) for c in courts_qs]
    
    return render(request, "homepage/index.html", {"court_list": court_list})

def court_detail(request, court_id):
    """Detail Page HTML"""
    court = get_object_or_404(Lapangan, id=court_id)
    
    is_favorited = False
    existing_label = "Lainnya"
    
    if request.user.is_authenticated:
        fav = LapanganFavorit.objects.filter(user=request.user, lapangan=court).first()
        if fav:
            is_favorited = True
            existing_label = fav.label

    formatted_price = f"{int(court.price):,}".replace(",", ".")

    return render(request, "homepage/court_detail.html", {
        "court": court,
        "formatted_price": formatted_price,
        "is_favorited": is_favorited,
        "existing_label": existing_label
    })

@login_required
def favorite_page_html(request):
    """
    Halaman Favorit (WADAH KOSONG).
    Datanya nanti diambil pake JavaScript (AJAX) dari API 'api_get_favorites'.
    """
    return render(request, 'homepage/favorite_list.html')

@login_required
def web_add_favorite(request, court_id):
    """
    Fallback Action khusus Web jika JS dimatikan (Redirect).
    """
    court = get_object_or_404(Lapangan, id=court_id)
    if LapanganFavorit.objects.filter(user=request.user, lapangan=court).exists():
        messages.warning(request, "Already in favorites!")
    else:
        if request.method == "POST":
            label = request.POST.get('label', 'Lainnya')
            LapanganFavorit.objects.create(user=request.user, lapangan=court, label=label)
            messages.success(request, "Added to favorites!")
    return redirect('homepage:court-detail', court_id=court_id)

@csrf_exempt
def api_get_all_courts(request):
    """
    API Utama untuk mengambil data lapangan dengan SEMUA Filter.
    Menghandle: Search (q), Location, Min Price, Max Price.
    """
    # 1. Ambil parameter
    q = request.GET.get("q", "").strip()
    location = request.GET.get("location", "").strip()
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    
    # 2. Queryset Awal
    qs = Lapangan.objects.all()

    # 3. Filter
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(location__icontains=q))
    
    if location:
        qs = qs.filter(location__icontains=location)
        
    try:
        if min_price not in (None, ""):
            qs = qs.filter(price__gte=int(min_price))
        if max_price not in (None, ""):
            qs = qs.filter(price__lte=int(max_price))
    except ValueError:
        pass 

    # 4. Serialize
    data = [serialize_lapangan(c) for c in qs]
    
    # 5. Return Dictionary results (Penting buat JS di template & Flutter)
    return JsonResponse({"status": "success", "results": data})

@csrf_exempt
def api_get_court_detail(request, court_id):
    try:
        court = Lapangan.objects.get(id=court_id)
        return JsonResponse(serialize_lapangan(court))
    except:
        return JsonResponse({"status": "error"}, status=404)

@csrf_exempt
@login_required
def api_get_favorites(request):
    """Mengambil list favorit user + Filter Label"""
    favorites = LapanganFavorit.objects.filter(user=request.user)
    
    label = request.GET.get('label')
    if label in ['Rumah', 'Kantor', 'Lainnya']:
        favorites = favorites.filter(label=label)
        
    data = [serialize_favorite_item(fav) for fav in favorites]
    return JsonResponse({"status": "success", "results": data}, safe=False)

@csrf_exempt
@require_POST
@login_required
def api_add_favorite(request, court_id):
    try:
        court = Lapangan.objects.get(id=court_id)
        if LapanganFavorit.objects.filter(user=request.user, lapangan=court).exists():
            return JsonResponse({"status": "exist", "message": "Already in favorites"}, status=409)
        
        label = "Lainnya"
        if request.body:
            try:
                label = json.loads(request.body).get('label', 'Lainnya')
            except: pass
        
        fav = LapanganFavorit.objects.create(user=request.user, lapangan=court, label=label)
        return JsonResponse({"status": "success", "data": serialize_favorite_item(fav)}, status=201)
    except:
        return JsonResponse({"status": "error"}, status=400)

@csrf_exempt
@require_POST
@login_required
def api_toggle_favorite(request, court_id):
    """
    API Cerdas: Kalau belum ada -> Add. Kalau sudah ada -> Remove.
    Cocok buat tombol Love.
    """
    try:
        court = Lapangan.objects.get(id=court_id)
        fav = LapanganFavorit.objects.filter(user=request.user, lapangan=court).first()

        if fav:
            # KONDISI 1: SUDAH ADA -> HAPUS (REMOVE)
            fav.delete()
            return JsonResponse({"status": "removed", "message": "Removed from favorites"})
        else:
            # KONDISI 2: BELUM ADA -> TAMBAH (ADD)
            label = "Lainnya"
            if request.body:
                try:
                    label = json.loads(request.body).get('label', 'Lainnya')
                except: pass
            
            LapanganFavorit.objects.create(user=request.user, lapangan=court, label=label)
            return JsonResponse({"status": "added", "message": "Added to favorites"})

    except Lapangan.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Court not found"}, status=404)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

@csrf_exempt
@require_POST
@login_required
def api_update_favorite(request, favorite_id):
    try:
        fav = LapanganFavorit.objects.get(id=favorite_id, user=request.user)
        new_label = None
        
        if request.body:
            try:
                new_label = json.loads(request.body).get('label')
            except: pass
        
        if not new_label: new_label = request.POST.get('label') 

        if new_label:
            fav.label = new_label
            fav.save()
            return JsonResponse({"status": "success", "message": "Label updated"})
        return JsonResponse({"status": "error"}, status=400)
    except:
        return JsonResponse({"status": "error"}, status=404)

@csrf_exempt
@require_POST
@login_required
def api_remove_favorite(request, favorite_id):
    try:
        LapanganFavorit.objects.get(id=favorite_id, user=request.user).delete()
        return JsonResponse({"status": "success"})
    except:
        return JsonResponse({"status": "error"}, status=404)

# Helper untuk URL lama biar ga error
def filter_courts(request):
    return api_get_all_courts(request)

def search_courts_ajax(request):
    return api_get_all_courts(request)