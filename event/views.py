from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .models import Event
from .forms import EventForm
from django.http import JsonResponse
from django.views.decorators.http import require_POST

# show semua event yang ada
def show_events(request):
    events = Event.objects.all().order_by('start_date')     # sort berdasarkan event
    context = {
        'events': events
    }
    return render(request, "show_event.html", context)

# show event's detail
def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    # cek dulu user sudah join event ini atau belum
    is_participant = False
    if request.user.is_authenticated:
        is_participant = event.participant.filter(id=request.user.id).exists()

    context = {
        'event': event,
        'is_participant': is_participant,
    }
    return render(request, "event_detail.html", context)

# create, edit, dan update event hanya untuk admin
@login_required(login_url='/login/')
def create_event(request):
    form = EventForm(request.POST or None)

    if form.is_valid() and request.method == "POST":
        event = form.save(commit=False)     # masih bisa edit
        event.admin = request.user          # adminnya adalah user yg lagi login
        event.save()
        messages.success(request, 'New event added!')
        return redirect('event:show_events')       # redirect ke halaman show event
    
    context = {
        'form': form
    }
    return render(request, "event_form.html", context)


@login_required(login_url='/login/')
def edit_event(request, pk):
    event = get_object_or_404(Event, pk=pk)

    # only admin yang bisa edit
    if request.user != event.admin:
        messages.error(request, 'You are not an admin')
        return redirect('event: event_detail', pk=pk)
    
    form = EventForm(request.POST or None, instance=event)

    if form.is_valid() and request.method == "POST":
        form.save()
        messages.success(request, 'Event updated!')
        return redirect('event: event_detail', pk=pk)
    
    context = {
        'form': form,
        'event': event
    }
    return render(request, "event_form.html", context)


@login_required(login_url='/login/')
def delete_event(request, pk):
    event = get_object_or_404(Event, pk=pk)     # ambil data event yang mau dihapus
    # only admin yang bisa delete
    if request.user != event.admin:
        messages.error(request, 'You are not an admin')
        return redirect('event: event_detail', pk=pk)
    
    # kalau request methodnya post, berarti user sudah confirm mau hapus
    if request.method == "POST":
        event.delete()
        messages.success(request, "Event deleted")
        return redirect('event:show_events')
    
    context = {'event': event}
    return render(request, "delete_event.html", context)

# method untuk join or cancel join event
@login_required(login_url='/login/')
def join_leave_event(request, pk):
    if request.method == 'POST':
        event = get_object_or_404(Event, pk=pk)
        user = request.user

        # cek apakah dia participat (sudah join) dari eventnya atau bukan
        is_participant = event.participant.filter(id=user.id).exists()

        if is_participant:
            # kalau dia participant berarti pas button diclick tuh dia mau cancel join (nanti tulisan buttonnya cancel join)
            event.participant.remove(user)
        else:
            # kalau belum join, cek kuota event
            if event.participant.count() >= event.max_participants:
                messages.error(request, f'Sorry, Event "{event.name}" is full and no longer accepting participant')
            else:
                event.participant.add(user)
                messages.success(request, f'You have joined this event!')
    
    return redirect('event:event_detail', pk=pk)

# buat versi ajax
@login_required(login_url='/login/')
@require_POST # fungsi hanya bisa diakses via POST
def join_event_ajax(request, pk):
    # fungsi ini mirip join_leave_event, tapi balasannya dalam bentuk JSON
    try:
        event = get_object_or_404(Event, pk=pk)
        user = request.user

        # cek apakah user sudah jadi participant atau udah join
        is_participant = event.participant.filter(id=user.id).exists()

        if is_participant:
            # jika sudah maka user ingin keluar
            event.participant.remove(user)
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
            event.participant.add(user)
            return JsonResponse({
                'status': 'success',
                'action': 'join', # aksinya adalah join
                'message': f'You successfully join event "{event.name}".',
                'new_participant_count': event.participant.count()
            })

    except Event.DoesNotExist:
        return JsonResponse({'status': 'fail', 'message': 'Event tidak ditemukan.'}, status=404)