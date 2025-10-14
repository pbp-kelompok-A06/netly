from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .models import Event
# from .forms import EventForm

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
        return redirect('show_event')       # redirect ke halaman show event
    
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
        return redirect('event_detail', pk=pk)
    
    form = EventForm(request.POST or None, instance=event)

    if form.is_valid() and request.method == "POST":
        form.save()
        messages.success(request, 'Event updated!')
        return redirect('event_detail', pk=pk)
    
    context = {
        'form': form,
        'event': event
    }
    return render(request, "event_form.html", context)

