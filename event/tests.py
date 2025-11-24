from django.test import TestCase, TransactionTestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.forms import ModelForm
from django.core.exceptions import ValidationError
from datetime import date, timedelta
import json
import uuid
from .models import Event
from .forms import EventForm
from authentication_user.models import UserProfile 

# tes untuk model
class EventModelTest(TestCase):
    # setup-nya kita buat user admin dulu
    def setUp(self):
        self.admin_user = User.objects.create_user(username='admin', password='123')
        self.admin_profile = UserProfile.objects.create(user=self.admin_user, role='admin')

    def test_event_creation(self):
        # tes bikin event baru
        event = Event.objects.create(
            admin=self.admin_profile,
            name="Turnamen Coba",
            description="Tes deskripsi",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=1),
            location="netlyyyyy",
            max_participants=10
        )
        # tes apakah namanya bener
        self.assertEqual(event.name, "Turnamen Coba")
        # tes apakah fungsi __str__ bener
        self.assertEqual(str(event), "Turnamen Coba")


# tes untuk form
class EventFormTest(TestCase):
    
    def test_form_valid(self):
        # tes kalo form-nya diisi bener
        form_data = {
            'name': 'Event Sah',
            'description': 'Deskripsi',
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=1), # tanggal selesai > tanggal mulai
            'location': 'Sana',
            'max_participants': 10
        }
        form = EventForm(data=form_data)
        self.assertTrue(form.is_valid()) # harusnya valid

    def test_form_invalid_missing_name(self):
        # tes kalo form-nya nggak diisi 'name' (wajib diisi)
        form_data = {
            'description': 'Deskripsi',
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=1),
            'location': 'Sana',
            'max_participants': 10
        }
        form = EventForm(data=form_data)
        self.assertFalse(form.is_valid()) # harusnya gagal
        self.assertIn('name', form.errors) # pastiin error-nya di 'name'

    def test_form_invalid_date(self):
        # tes kalo tanggal selesainya salah (sebelum tanggal mulai)
        form_data = {
            'name': 'Event Gagal Tanggal',
            'description': 'Deskripsi',
            'start_date': date.today(),
            'end_date': date.today() - timedelta(days=1),
            'location': 'Sana',
            'max_participants': 10
        }
        form = EventForm(data=form_data)
        self.assertFalse(form.is_valid()) 
        self.assertIn('end_date', form.errors) # make sure error-nya di 'end_date'


# tes untuk semua views.py
# kita pakai TransactionTestCase biar lebih aman buat ngetes AJAX/JSON
class EventViewTest(TransactionTestCase):

    def setUp(self):
        # ini dijalanin pertama kali
        # kita butuh 2 tipe user: admin dan user biasa
        self.client = Client()

        # user admin
        self.admin_user = User.objects.create_user(username='admin', password='123')
        self.admin_profile = UserProfile.objects.create(user=self.admin_user, role='admin')

        # user biasa
        self.normal_user = User.objects.create_user(username='userbiasa', password='123')
        self.normal_profile = UserProfile.objects.create(user=self.normal_user, role='user')

        # kita bikin 1 event buat bahan tes
        self.event1 = Event.objects.create(
            admin=self.admin_profile,
            name="Event yang Sudah Ada",
            description="Tes deskripsi",
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=11),
            location="Sini",
            max_participants=10
        )
        
        # ini data buat nge-post form
        self.valid_event_data = {
            'name': 'Event Baru',
            'description': 'Deskripsi baru',
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=1),
            'location': 'Lokasi Baru',
            'max_participants': 5
        }


    def test_show_events_page(self):
        # tes halaman utama event (show_events)
        self.client.login(username='userbiasa', password='123')
        response = self.client.get(reverse('event:show_events'))
        self.assertEqual(response.status_code, 200) # 200 berarti oke
        
        self.assertContains(response, "Badminton")
        self.assertContains(response, "Events")
        self.assertContains(response, "Sort Date: Earliest") # cek sorting default

    def test_show_events_sort_descending(self):
        # tes halaman utama kalo di-sort 'desc'
        self.client.login(username='userbiasa', password='123')
        response = self.client.get(reverse('event:show_events') + "?sort=desc")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sort Date: Latest") # cek label sorting
    
    def test_event_detail_page(self):
        # tes halaman detail
        self.client.login(username='userbiasa', password='123')
        url = reverse('event:event_detail', args=[self.event1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Event yang Sudah Ada") # cek ada nama eventnya
        self.assertContains(response, "Join") # cek ada tombol join

    def test_event_detail_logic(self):
        # tes logika di halaman detail (event penuh, event lewat)
        self.client.login(username='userbiasa', password='123')
        # bikin event penuh
        event_penuh = Event.objects.create(
            admin=self.admin_profile, name="Event Penuh", start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=2), location="Sana", max_participants=0 # max 0 = auto penuh
        )
        
        # bikin event lewat
        event_lewat = Event.objects.create(
            admin=self.admin_profile, name="Event Lewat", start_date=date.today() - timedelta(days=2),
            end_date=date.today() - timedelta(days=1), location="Sana", max_participants=10
        )

        # cek halaman event penuh
        url_penuh = reverse('event:event_detail', args=[event_penuh.id])
        response_penuh = self.client.get(url_penuh)
        self.assertContains(response_penuh, "Event is Full") # harus ada tulisan 'Event is Full'

        # cek halaman event lewat
        url_lewat = reverse('event:event_detail', args=[event_lewat.id])
        response_lewat = self.client.get(url_lewat)
        self.assertContains(response_lewat, "Event Has Ended") # harus ada tulisan 'Event Has Ended'
        
    # test create pake ajax
    def test_create_event_ajax_admin(self):
        # tes bikin event kalo dia admin (harus berhasil)
        self.client.login(username='admin', password='123')
        response = self.client.post(reverse('event:create_event_ajax'), self.valid_event_data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success') # cek balasan JSON
        self.assertTrue(Event.objects.filter(name='Event Baru').exists()) # cek eventnya beneran dibuat

    def test_create_event_ajax_non_admin(self):
        # tes bikin event kalo dia user biasa (harus ditolak 403)
        self.client.login(username='userbiasa', password='123')
        response = self.client.post(reverse('event:create_event_ajax'), self.valid_event_data)
        
        self.assertEqual(response.status_code, 403) # 403 = Forbidden

    def test_create_event_ajax_not_logged_in(self):
        # tes bikin event kalo belum login (harus redirect)
        response = self.client.post(reverse('event:create_event_ajax'), self.valid_event_data)
        
        self.assertEqual(response.status_code, 302) # 302 = Redirect (ke halaman login)

    def test_create_event_ajax_invalid_data(self):
        # tes bikin event tapi datanya salah (misal nama tidak diisi)
        self.client.login(username='admin', password='123')
        invalid_data = self.valid_event_data.copy()
        del invalid_data['name'] # hapus field 'name' yang wajib diisi
        
        response = self.client.post(reverse('event:create_event_ajax'), invalid_data)
        
        self.assertEqual(response.status_code, 400) # 400 = Bad Request
        self.assertEqual(response.json()['status'], 'fail')
        self.assertIn('name', response.json()['errors'])

    # test edit ajax
    def test_edit_event_ajax_admin(self):
        # tes edit event kalo dia admin (harus berhasil)
        self.client.login(username='admin', password='123')
        url = reverse('event:edit_event_ajax', args=[self.event1.id])
        
        edit_data = self.valid_event_data.copy()
        edit_data['name'] = "Nama Sudah Di-edit" # kita ganti namanya
        
        response = self.client.post(url, edit_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        
        # cek di database apakah namanya beneran ganti
        self.event1.refresh_from_db() # ambil data terbaru dari db
        self.assertEqual(self.event1.name, "Nama Sudah Di-edit")

    def test_edit_event_ajax_not_the_admin(self):
        # tes edit event, tapi dia admin lain (bukan yang bikin event)
        # bikin admin baru
        admin_lain = User.objects.create_user(username='admin2', password='123')
        UserProfile.objects.create(user=admin_lain, role='admin')
        
        self.client.login(username='admin2', password='123') # login sebagai admin2
        url = reverse('event:edit_event_ajax', args=[self.event1.id]) # event1 dibuat oleh 'admin'
        
        response = self.client.post(url, self.valid_event_data)
        self.assertEqual(response.status_code, 403) # harus dilarang (Forbidden)
    
    # test delete ajax
    def test_delete_event_ajax_admin(self):
        # tes hapus event kalo dia admin (harus berhasil)
        self.client.login(username='admin', password='123')
        url = reverse('event:delete_event_ajax', args=[self.event1.id])
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        
        # cek dan make sure eventnya ilang
        self.assertFalse(Event.objects.filter(id=self.event1.id).exists())
    
    def test_delete_event_ajax_non_admin(self):
        # tes hapus event kalo dia user biasa (harus ditolak 403)
        self.client.login(username='userbiasa', password='123')
        url = reverse('event:delete_event_ajax', args=[self.event1.id])
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403) # 403 = Forbidden
        
    def test_delete_event_not_found(self):
        # tes hapus event tapi event-nya nggak ada (pakai UUID palsu)
        self.client.login(username='admin', password='123')
        fake_uuid = uuid.uuid4()
        url = reverse('event:delete_event_ajax', args=[fake_uuid])
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404) # 404 = Not Found
        
    # test get json
    def test_get_event_json_admin(self):
        # tes ambil data JSON buat form edit (harus berhasil)
        self.client.login(username='admin', password='123')
        url = reverse('event:get_event_json', args=[self.event1.id])
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        self.assertEqual(response.json()['data']['name'], self.event1.name) # cek datanya bener

    def test_get_event_json_non_admin(self):
        # tes ambil data JSON tapi dia user biasa (harus dilarang)
        self.client.login(username='userbiasa', password='123')
        url = reverse('event:get_event_json', args=[self.event1.id])
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403) # 403 = Forbidden

    # test join leave ajax
    def test_join_event_ajax(self):
        # tes user biasa join event (harus berhasil)
        self.client.login(username='userbiasa', password='123')
        url = reverse('event:join_event_ajax', args=[self.event1.id])
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['action'], 'join') # aksinya 'join'
        self.assertEqual(data['new_participant_count'], 1) # pesertanya jadi 1
        
        # cek di database
        self.assertTrue(self.event1.participant.filter(user=self.normal_user).exists())

    def test_leave_event_ajax(self):
        # tes user keluar dari event (harus berhasil)
        # 1. kita joinkan dulu usernya
        self.event1.participant.add(self.normal_profile)
        
        # 2. baru kita tes keluar
        self.client.login(username='userbiasa', password='123')
        url = reverse('event:join_event_ajax', args=[self.event1.id])
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['action'], 'leave') # aksinya 'leave'
        self.assertEqual(data['new_participant_count'], 0) # pesertanya jadi 0
        
        # cek di database
        self.assertFalse(self.event1.participant.filter(user=self.normal_user).exists())
        
    def test_join_event_full_ajax(self):
        # tes join event tapi udah penuh (harus gagal)
        # 1. bikin event penuh
        event_penuh = Event.objects.create(
            admin=self.admin_profile, name="Event Penuh", start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=2), location="Sana", max_participants=0 # max 0 = penuh
        )
        
        # 2. tes join
        self.client.login(username='userbiasa', password='123')
        url = reverse('event:join_event_ajax', args=[event_penuh.id])
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400) # 400 = Bad Request
        self.assertEqual(response.json()['status'], 'fail')
        self.assertEqual(response.json()['message'], 'Maaf, event sudah penuh.')