from datetime import date, timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .models import Event
from .forms import EventForm
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.http import require_POST
from django.forms.models import model_to_dict
import json
from django.views.decorators.csrf import csrf_exempt

def is_admin(user):
    return hasattr(user, 'profile') and user.profile.role == 'admin'

# untuk admin authentication -> untuk function yang hanya bisa diakses oleh admin
def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('authentication_user:login')
        if not is_admin(request.user):
            return HttpResponseForbidden("You don't have permission to access this page.")
        return view_func(request, *args, **kwargs)
    return wrapper

# ambil data dalam format JSON untuk pre-fill form edit
@login_required(login_url='/login/')
def get_event_json(request, pk):
    try:
        event = Event.objects.get(pk=pk)
        if request.user.profile != event.admin:
            return JsonResponse({'status': 'fail', 'message': 'Bukan admin'}, status=403)
        
        # ubah tanggal jadi string with .isoformat()
        event_data = {
            'id': event.id,
            'name': event.name,
            'description': event.description,
            'start_date': event.start_date.isoformat(), 
            'end_date': event.end_date.isoformat(),    
            'location': event.location,
            'image_url': event.image_url,
            'max_participants': event.max_participants,
        }
        
        # jadikan datanya sebagai response
        return JsonResponse({'status': 'success', 'data': event_data})
    except Event.DoesNotExist:
        return JsonResponse({'status': 'fail', 'message': 'Event tidak ditemukan'}, status=404)
    
# show semua event yang ada
@login_required(login_url='/login/')
def show_events(request):
    # ambil parameter sort dari URL, defaultnya ascending
    sort_order = request.GET.get('sort', 'asc')

    # tentukan urutan based on parameter sort
    if sort_order == 'desc':
        # '-start_date' berarti descending (terbaru/latest)
        order_by_field = '-start_date'
        sort_label = 'Latest'
    else:
        # 'start_date' berarti ascending (terlama/earliest)
        order_by_field = 'start_date'
        sort_label = 'Earliest'

    # ambilevent dari database dengan urutan yang benar
    events = Event.objects.all().order_by(order_by_field)
    
    context = {
        'events': events,
        'current_sort_label': sort_label        
    }
    return render(request, "show_event.html", context)

# show event's detail
@login_required(login_url='/login/')
def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    
    # cek dulu user sudah join event ini atau belum
    is_participant = False
    if request.user.is_authenticated:
        is_participant = event.participant.filter(id=request.user.profile.id).exists()

    # cek apakah event sudah lewat atau belum
    is_event_active = event.start_date > date.today()
    # cek apakah kuota sudah penuh
    is_event_full = event.participant.count() >= event.max_participants

    context = {
        'event': event,
        'is_participant': is_participant,
        'is_event_active': is_event_active, 
        'is_event_full': is_event_full,   
    }
    return render(request, "event_detail.html", context)

# [CRUD] create, edit, dan update event hanya untuk admin -> user hanya bisa lihat dan join

# handle create event melalui AJAX modal
@admin_required
@login_required(login_url='/login/')
@require_POST
def create_event_ajax(request):
    form = EventForm(request.POST or None)

    if form.is_valid():
        event = form.save(commit=False)
        event.admin = request.user.profile          # adminnya adalah user yg lagi login
        event.save()
        return JsonResponse({'status': 'success', 'message': 'Event baru berhasil dibuat!'})
    else:
        return JsonResponse({'status': 'fail', 'errors': form.errors}, status=400)

# handle edit event
@admin_required
@login_required(login_url='/login/')
@require_POST
def edit_event_ajax(request, pk):
    try:
        # get event sesuai dengan primary keynya
        event = Event.objects.get(pk=pk)
        
        if request.user.profile != event.admin:
            return JsonResponse({'status': 'fail', 'message': 'Bukan admin'}, status=403)
            
        form = EventForm(request.POST or None, instance=event)
        
        if form.is_valid():
            form.save()
            updated_event_data = { 
                'id': event.id,
                'name': event.name,
                'start_date': event.start_date.isoformat(),
                'end_date': event.end_date.isoformat(),    
                'location': event.location,
                'image_url': event.image_url,
                'max_participants': event.max_participants,
            }
            return JsonResponse({
                'status': 'success', 
                'message': 'Event berhasil diperbarui.',
                'updated_event': updated_event_data         # kirim updated data supaya auto update (no refresh)
            })
        else:
            return JsonResponse({'status': 'fail', 'errors': form.errors}, status=400)
            
    except Event.DoesNotExist:
        return JsonResponse({'status': 'fail', 'message': 'Event tidak ditemukan'}, status=404)

@login_required(login_url='/login/')
@admin_required
@require_POST
def delete_event_ajax(request, pk):
    try:
        event = Event.objects.get(pk=pk)
        if request.user.profile != event.admin:
            return JsonResponse({'status': 'fail', 'message': 'Bukan admin'}, status=403)
        
        event.delete()
        return JsonResponse({'status': 'success', 'message': 'Event berhasil dihapus.'})
    except Event.DoesNotExist:
        return JsonResponse({'status': 'fail', 'message': 'Event tidak ditemukan'}, status=404)

# method untuk join or cancel join event
@login_required(login_url='/login/')
def join_leave_event(request, pk):
    if request.method == 'POST':
        event = get_object_or_404(Event, pk=pk)
        user_profile = request.user.profile

        # cek apakah participat udah join dari eventnya
        is_participant = event.participant.filter(id=user_profile.id).exists()

        if is_participant:
            # kalau dia participant berarti pas button diclick dia mau cancel join (nanti tulisan buttonnya cancel join)
            event.participant.remove(user_profile)
            messages.info(request, f'You have canceled your participation on "{event.name}".')
        else:
            # kalau belum join, cek kuota event
            if event.participant.count() >= event.max_participants:
                messages.error(request, f'Sorry, Event "{event.name}" is full and no longer accepting participant')
            else:
                event.participant.add(user_profile)
                messages.success(request, f'You have joined this event!')
    
    return redirect('event:event_detail', pk=pk)

# buat versi ajax
@login_required(login_url='/login/')
@require_POST 
def join_event_ajax(request, pk):
    # fungsi ini mirip join_leave_event, tapi returnnya dalam bentuk JSON
    try:
        event = get_object_or_404(Event, pk=pk)
        user_profile = request.user.profile

        # cek apakah user sudah jadi participant atau udah join
        is_participant = event.participant.filter(id=user_profile.id).exists()

        if is_participant:
            # jika sudah maka user ingin keluar
            event.participant.remove(user_profile)
            return JsonResponse({
                'status': 'success',
                'action': 'leave', # kita kasih info aksinya apa
                'message': f'Anda berhasil keluar dari event "{event.name}".',
                'new_participant_count': event.participant.count()
            })
        else:
            # jika belum cek kuota event berapa max participantsnya
            if event.participant.count() >= event.max_participants:
                return JsonResponse({'status': 'fail', 'message': 'Maaf, event sudah penuh.'}, status=400)
            
            # jika aman tambahkan user
            event.participant.add(user_profile)
            return JsonResponse({
                'status': 'success',
                'action': 'join', # aksinya adalah join
                'message': f'You successfully join event "{event.name}".',
                'new_participant_count': event.participant.count()
            })

    except Event.DoesNotExist:
        return JsonResponse({'status': 'fail', 'message': 'Event tidak ditemukan.'}, status=404)
    
def show_events_flutter(request):
    events = Event.objects.all().order_by('start_date')
    data = []
    
    for event in events:
        is_joined_status = False 
        
        # apakah user sedang login dan punya profile?
        if request.user.is_authenticated and hasattr(request.user, 'profile'):
            is_joined_status = event.participant.filter(id=request.user.profile.id).exists()

        data.append({
            "pk": str(event.id),
            "fields": {
                "name": event.name,
                "description": event.description,
                "start_date": event.start_date.isoformat(),
                "end_date": event.end_date.isoformat(),
                "location": event.location,
                "image_url": event.image_url,
                "max_participants": event.max_participants,
                "participant_count": event.participant.count(),
                "is_active": event.start_date > date.today(),
                # apakah event udah full? detect pake jumlah participant dan max participantsnya
                "is_full": event.participant.count() >= event.max_participants,
                # cek apakah user yang login sudah join
                "is_joined": is_joined_status
            }
        })
        
    return JsonResponse(data, safe=False)

@csrf_exempt
def create_event_flutter(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body) # decode JSON body req
            user_profile = request.user.profile # ini harusnya admin karena create cuma bisa dilakuin sama admin

            new_event = Event.objects.create(
                admin=user_profile,     # assign pemilik atau pembuat event
                name=data["name"],
                description=data["description"],
                start_date=data["start_date"], 
                end_date=data["end_date"],
                location=data["location"],
                max_participants=int(data["max_participants"]),
                image_url=data.get("image_url", "") 
            )
            
            new_event.save()
            return JsonResponse({"status": "success"}, status=200)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    
    return JsonResponse({"status": "error", "message": "Invalid method"}, status=401)

@csrf_exempt
def edit_event_flutter(request, pk):
    try:
        # ambil objek event dulu
        event = Event.objects.get(pk=pk)
    except Event.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Event tidak ditemukan'}, status=404)

    if request.method == 'POST':
        data = json.loads(request.body)
        
        # validasi Admin
        if request.user.profile != event.admin:
             return JsonResponse({'status': 'error', 'message': 'Bukan admin'}, status=403)

        # update attribute event yang udah kita get sebelumnya
        event.name = data["name"]
        event.description = data["description"]
        event.start_date = data["start_date"]
        event.end_date = data["end_date"]
        event.location = data["location"]
        event.max_participants = int(data["max_participants"])
        event.image_url = data.get("image_url", event.image_url)
        
        event.save()
        return JsonResponse({"status": "success", "message": "Event berhasil diupdate"}, status=200)

    return JsonResponse({"status": "error"}, status=401)

@csrf_exempt
@require_POST
def join_event_flutter(request, pk):
    try:
        event = Event.objects.get(pk=pk)

        if not request.user.is_authenticated:
             return JsonResponse({'status': 'fail', 'message': 'Please login first'}, status=401)
     
        user_profile = request.user.profile

        # cek apakah event udah lewat
        if event.end_date < date.today():
             return JsonResponse({'status': 'fail', 'message': 'Event has ended'}, status=400)

        # kalau user exists, berarti user sudah join dan mau leave, jadi harus kita remove
        if event.participant.filter(id=user_profile.id).exists():
            event.participant.remove(user_profile)
            return JsonResponse({'status': 'success', 'action': 'leave', 'message': 'Left event'})
        else:
            # kalau belum join, maka dia mau join event dan kita harus cek kuota dulu
            if event.participant.count() >= event.max_participants:
                return JsonResponse({'status': 'fail', 'message': 'Full'}, status=400)
            
            event.participant.add(user_profile)
            return JsonResponse({'status': 'success', 'action': 'join', 'message': 'Joined event'})
            
    except Event.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Not found'}, status=404)


@csrf_exempt
def delete_event_flutter(request, pk):
    if request.method == 'POST':
        try:
            event = Event.objects.get(pk=pk)
            # cek apakah user adalah admin dari event tersebut
            if request.user.profile != event.admin:
                return JsonResponse({'status': 'error', 'message': 'Bukan admin'}, status=403)
            
            event.delete()
            return JsonResponse({'status': 'success', 'message': 'Event berhasil dihapus'})
        except Event.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Event tidak ditemukan'}, status=404)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=401)

