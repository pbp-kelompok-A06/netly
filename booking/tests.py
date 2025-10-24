from django.test import TestCase
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User


# Asumsi UserProfile ada di app 'authentication_user'
from authentication_user.models import UserProfile

from admin_lapangan.models import Lapangan
from admin_lapangan.models import JadwalLapangan as Jadwal

from .models import Booking
from django.utils import timezone
from datetime import timedelta


class ShowJsonViewTest(TestCase):

    def setUp(self):
        """Siapkan data 'palsu' yang akan digunakan untuk semua tes."""

        # 1. Buat dua user berbeda
        self.user1 = User.objects.create_user(username='user1', password='password123')
        self.user2 = User.objects.create_user(username='user2', password='password123')

        # 2. Buat profil mereka
        # (Kita buat manual agar tes tidak bergantung pada signals)
        self.profile1 = UserProfile.objects.create(user=self.user1, fullname="User Satu")
        self.profile2 = UserProfile.objects.create(user=self.user2, fullname="User Dua")

        # 3. Buat data lapangan dan jadwal
        self.lapangan_a = Lapangan.objects.create(
            name="Lapangan A", 
            price=100000,
            admin=self.user1 
        )
        self.jadwal_senin = Jadwal.objects.create(
            lapangan=self.lapangan_a,
            tanggal='2025-10-27', 
            start_main='10:00:00', 
            end_main='11:00:00'
        )
        self.jadwal_selasa = Jadwal.objects.create(
            lapangan=self.lapangan_a,
            tanggal='2025-10-28', 
            start_main='14:00:00', 
            end_main='15:00:00'
        )

        # 4. Buat booking untuk user1
        self.booking1 = Booking.objects.create(
            user_id=self.profile1,
            lapangan_id=self.lapangan_a,
            status_book='pending'
        )
        self.booking1.jadwal.add(self.jadwal_senin)
        
        # 5. Buat booking untuk user2 (untuk memastikan view bisa memfilter)
        self.booking2 = Booking.objects.create(
            user_id=self.profile2,
            lapangan_id=self.lapangan_a,
            status_book='completed'
        )
        self.booking2.jadwal.add(self.jadwal_selasa)

        # 6. Siapkan client dan URL
        self.client = Client()
        # Pastikan app_name='booking' dan name='show_json' di urls.py
        self.url = reverse('booking:show_json') 
        self.url_create_booking = reverse('booking:create_booking')
        self.today = timezone.now().date()
        
        # Skenario 1: (HARUS MUNCUL) Jadwal hari ini, tersedia
        self.jadwal_valid_today = Jadwal.objects.create(
            lapangan=self.lapangan_a,
            tanggal=self.today,
            start_main='15:00:00', end_main='16:00:00',
            is_available=True
        )
        
        # Skenario 2: (HARUS MUNCUL) Jadwal 2 hari lagi, tersedia
        self.jadwal_valid_plus_2 = Jadwal.objects.create(
            lapangan=self.lapangan_a,
            tanggal=self.today + timedelta(days=2),
            start_main='15:00:00', end_main='16:00:00',
            is_available=True
        )
        
        # Skenario 3: (Filter Tanggal) Jadwal kemarin, tersedia
        self.jadwal_past = Jadwal.objects.create(
            lapangan=self.lapangan_a,
            tanggal=self.today - timedelta(days=1),
            start_main='15:00:00', end_main='16:00:00',
            is_available=True
        )
        
        # Skenario 4: (Filter Tanggal) Jadwal 3 hari lagi, tersedia
        self.jadwal_future = Jadwal.objects.create(
            lapangan=self.lapangan_a,
            tanggal=self.today + timedelta(days=3),
            start_main='15:00:00', end_main='16:00:00',
            is_available=True
        )
        
        # Skenario 5: (Filter is_available) Jadwal hari ini, TIDAK tersedia
        self.jadwal_not_available = Jadwal.objects.create(
            lapangan=self.lapangan_a,
            tanggal=self.today,
            start_main='17:00:00', end_main='18:00:00',
            is_available=False
        )
        
        # Skenario 6: (Filter Lapangan) Jadwal hari ini, tersedia, TAPI di Lapangan B
        # Kita perlu buat lapangan B dulu (dimiliki user2_player, misalnya)
        self.lapangan_b = Lapangan.objects.create(
             name="Lapangan B", price=50000, admin=self.user2 
        )
        self.jadwal_wrong_lapangan = Jadwal.objects.create(
            lapangan=self.lapangan_b, # <-- Perhatikan: lapangan_b
            tanggal=self.today,
            start_main='15:00:00', end_main='16:00:00',
            is_available=True
        )
        
        # Simpan URL untuk tes
        self.url_show_create_A = reverse('booking:show_create_booking', kwargs={'lapangan_id': self.lapangan_a.id})
    def test_show_create_booking_filters_correctly(self):
        """
        TES: (Logic) Pastikan view HANYA menampilkan jadwal yang:
        1. Milik lapangan_a
        2. is_available=True
        3. Tanggalnya >= hari ini DAN <= hari ini + 2 hari
        """
        # View ini tidak dilindungi @login_required, jadi kita bisa langsung panggil
        response = self.client.get(self.url_show_create_A)
        
        # Cek 1: Halaman berhasil di-render
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_book.html')
        
        # Cek 2: Konteks lapangan benar
        self.assertEqual(response.context['lapangan'], self.lapangan_a)
        
        # Cek 3: Konteks 'jadwals' berisi data yang TEPAT
        jadwals_in_context = response.context['jadwals']
        
        # HARUS HANYA ADA 2 jadwal yang lolos filter
        self.assertEqual(jadwals_in_context.count(), 2)
        
        # Pastikan yang valid ADA di dalam list
        self.assertIn(self.jadwal_valid_today, jadwals_in_context)
        self.assertIn(self.jadwal_valid_plus_2, jadwals_in_context)
        
        # Pastikan yang tidak valid (karena alasan berbeda) TIDAK ADA
        self.assertNotIn(self.jadwal_past, jadwals_in_context)
        self.assertNotIn(self.jadwal_future, jadwals_in_context)
        self.assertNotIn(self.jadwal_not_available, jadwals_in_context)
        self.assertNotIn(self.jadwal_wrong_lapangan, jadwals_in_context)
        
        # Pastikan jadwal lama (hardcoded) juga tidak ada (karena di luar range tanggal)
        self.assertNotIn(self.jadwal_senin, jadwals_in_context)
        self.assertNotIn(self.jadwal_selasa, jadwals_in_context)
        
    def test_show_create_booking_404_if_lapangan_invalid(self):
        """
        TES: (Error) Pastikan view mengembalikan 404 jika UUID lapangan tidak ada.
        """
        # Buat UUID palsu
        invalid_uuid = '00000000-0000-0000-0000-000000000000'
        url = reverse('booking:show_create_booking', kwargs={'lapangan_id': invalid_uuid})
        
        response = self.client.get(url)
        
        # View menggunakan get_object_or_404, jadi harus 404
        self.assertEqual(response.status_code, 404)
    def test_show_json_unauthenticated(self):
        """
        TES 1: Pastikan user yang belum login di-redirect ke halaman login.
        (Ini mengasumsikan kamu sudah menambah @login_required di view)
        """
        response = self.client.get(self.url)
        
        # 302 adalah status code untuk redirect
        self.assertEqual(response.status_code, 302)
        # Pastikan redirect ke URL login (sesuaikan '/login/' jika beda)
        self.assertIn('/login/', response.url)

    def test_show_json_authenticated_user_sees_own_bookings(self):
        """
        TES 2: Pastikan user1 yang login HANYA melihat booking miliknya.
        """
        # Login sebagai user1
        self.client.login(username='user1', password='password123')
        
        response = self.client.get(self.url)
        
        # 1. Cek status dan tipe konten
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # 2. Parse data JSON
        data = response.json()
        
        # 3. Cek data
        self.assertIsInstance(data, list)
        # HARUS HANYA 1 booking, yaitu milik user1
        self.assertEqual(len(data), 1) 
        
        # 4. Cek detail data (spot check)
        booking_data = data[0]
        self.assertEqual(booking_data['id'], str(self.booking1.id))
        self.assertEqual(booking_data['lapangan']['name'], 'Lapangan A')
        self.assertEqual(booking_data['user']['id'], str(self.profile1.id))
        self.assertEqual(booking_data['status_book'], 'pending')
        self.assertEqual(len(booking_data['jadwal']), 1)
        self.assertEqual(booking_data['jadwal'][0]['start_main'], '10:00:00')
        # Cek apakah total_price() dipanggil (asumsi total_price = 100000)
        self.assertEqual(int(float(booking_data['total_price'])), 100000)

    def test_show_json_authenticated_user_no_bookings(self):
        """
        TES 3: Pastikan user baru yang tidak punya booking mendapat list kosong.
        """
        # Buat user baru tanpa booking
        user3 = User.objects.create_user(username='user3', password='password123')
        UserProfile.objects.create(user=user3, fullname="User Tiga")
        
        # Login sebagai user3
        self.client.login(username='user3', password='password123')
        
        response = self.client.get(self.url)
        
        # Cek status
        self.assertEqual(response.status_code, 200)
        
        # Cek data
        data = response.json()
        self.assertEqual(data, []) # List harus kosong
    
    # Tambahkan ini di dalam class ShowJsonViewTest di booking/tests.py

    def test_complete_booking_success(self):
        """
        TES 1: (Happy Path) Pastikan user1 bisa complete booking miliknya
        yang statusnya 'pending'.
        """
        # 1. Login sebagai user1
        self.client.login(username='user1', password='password123')
        
        # 2. Tentukan URL (harus pakai reverse() untuk booking spesifik)
        url = reverse('booking:complete_booking', kwargs={'booking_id': self.booking1.id})
        
        # 3. Kirim request POST (sesuai 'fetch' di JS)
        response = self.client.post(url)
        
        # 4. Cek respons JSON
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'Completed')
        
        # 5. Cek database (PALING PENTING)
        # Ambil data booking1 terbaru dari database
        self.booking1.refresh_from_db() 
        self.assertEqual(self.booking1.status_book, 'completed')

    def test_complete_booking_not_authorized(self):
        """
        TES 2: (Security) Pastikan user1 GAGAL complete booking milik user2.
        """
        # 1. Login sebagai user1
        self.client.login(username='user1', password='password123')
        
        # 2. Tentukan URL, tapi pakai ID booking2 (milik user2)
        url = reverse('booking:complete_booking', kwargs={'booking_id': self.booking2.id})
        
        # 3. Kirim request POST
        response = self.client.post(url)
        
        # 4. Cek respons (Harus 404, sesuai 'Booking.DoesNotExist')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['message'], 'Booking not found or not authorized')

    def test_complete_booking_not_logged_in(self):
        """
        TES 3: (Security) Pastikan user yang belum login di-redirect.
        """
        # 1. (Jangan login)
        
        # 2. Tentukan URL
        url = reverse('booking:complete_booking', kwargs={'booking_id': self.booking1.id})
        
        # 3. Kirim request POST
        response = self.client.post(url)
        
        # 4. Cek respons (Harus 302 Redirect ke login)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url) # (Sesuaikan jika URL login-mu beda)

    def test_complete_booking_already_completed(self):
        """
        TES 4: (Logic) Pastikan user GAGAL complete booking yang
        statusnya sudah 'completed'.
        """
        # 1. Login sebagai user2 (pemilik booking2)
        self.client.login(username='user2', password='password123')
        
        # 2. Tentukan URL (pakai booking2, yang statusnya 'completed')
        url = reverse('booking:complete_booking', kwargs={'booking_id': self.booking2.id})
        
        # 3. Kirim request POST
        response = self.client.post(url)
        
        # 4. Cek respons
        self.assertEqual(response.status_code, 200)
        self.assertIn('Booking is already completed', response.json()['message'])

    def test_complete_booking_failed_status(self):
        """
        TES 5: (Logic) Pastikan user GAGAL complete booking yang
        statusnya 'failed'.
        """
        # 1. Ubah dulu status booking1 jadi 'failed'
        self.booking1.status_book = 'failed'
        self.booking1.save()
        
        # 2. Login sebagai user1 (pemilik booking1)
        self.client.login(username='user1', password='password123')
        
        # 3. Tentukan URL
        url = reverse('booking:complete_booking', kwargs={'booking_id': self.booking1.id})
        
        # 4. Kirim request POST
        response = self.client.post(url)
        
        # 5. Cek respons
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['message'], 'Booking has expired and cannot be completed')
    
    # -----------------------------------------------
    # TES UNTUK VIEW CREATE_BOOKING
    # -----------------------------------------------

    def test_create_booking_success(self):
        """
        TES 1: (Happy Path) Pastikan user1 bisa create booking baru.
        """
        # 1. Login sebagai user1
        self.client.login(username='user1', password='password123')
        
        # 2. Siapkan data POST
        # Pastikan kita booking jadwal yang 'is_available=True' (jadwal_senin)
        self.assertTrue(self.jadwal_senin.is_available)
        post_data = {
            'lapangan_id': self.lapangan_a.id,
            'jadwal_id': [self.jadwal_senin.id] # 'getlist' butuh format list
        }

        # 3. Kirim request POST
        response = self.client.post(self.url_create_booking, data=post_data)
        
        # 4. Cek respons JSON
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('payment_url', data) # Pastikan payment_url dikirim
        
        # 5. Cek Database (PALING PENTING)
        # Pastikan booking baru dibuat (total jadi 3)
        self.assertEqual(Booking.objects.count(), 3) 
        new_booking = Booking.objects.get(id=data['booking_id'])
        self.assertEqual(new_booking.user_id, self.profile1)
        self.assertEqual(new_booking.lapangan_id, self.lapangan_a)
        
        # 6. Cek M2M relation (jadwal)
        self.assertEqual(new_booking.jadwal.count(), 1)
        self.assertEqual(new_booking.jadwal.first(), self.jadwal_senin)

        # 7. Cek side-effect (jadwal jadi not available)
        self.jadwal_senin.refresh_from_db()
        self.assertFalse(self.jadwal_senin.is_available)

    def test_create_booking_jadwal_not_available(self):
        """
        TES 2: (Validation) Pastikan GAGAL jika jadwal.is_available=False.
        """
        # 1. Login sebagai user1
        self.client.login(username='user1', password='password123')

        # 2. Siapkan data POST, tapi pakai jadwal_selasa
        #    Lalu, kita set jadwal_selasa jadi 'not available'
        self.jadwal_selasa.is_available = False
        self.jadwal_selasa.save()
        
        post_data = {
            'lapangan_id': self.lapangan_a.id,
            'jadwal_id': [self.jadwal_selasa.id]
        }

        # 3. Kirim request POST
        response = self.client.post(self.url_create_booking, data=post_data)
        
        # 4. Cek respons JSON
        self.assertEqual(response.status_code, 400) # Sesuai view kamu
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('already booked or invalid', data['message'])
        
        # 5. Cek Database (Pastikan tidak ada booking baru yang dibuat)
        self.assertEqual(Booking.objects.count(), 2) # Harus tetap 2

    def test_create_booking_not_logged_in(self):
        """
        TES 3: (Security) Pastikan user yang belum login di-redirect.
        """
        # 1. (Jangan login)
        post_data = {
            'lapangan_id': self.lapangan_a.id,
            'jadwal_id': [self.jadwal_senin.id]
        }
        
        # 2. Kirim request POST
        response = self.client.post(self.url_create_booking, data=post_data)
        
        # 3. Cek respons (Harus 302 Redirect ke login)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url) # (Sesuaikan jika URL login-mu beda)

    def test_create_booking_wrong_method(self):
        """
        TES 4: (Logic) Pastikan GAGAL jika pakai method GET.
        """
        # 1. Login sebagai user1
        self.client.login(username='user1', password='password123')
        
        # 2. Kirim request GET
        response = self.client.get(self.url_create_booking)
        
        # 3. Cek respons JSON
        self.assertEqual(response.status_code, 405) # Sesuai view kamu
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'Invalid request method.')
    
    # -----------------------------------------------
    # TES UNTUK VIEW CREATE_BOOKING
    # -----------------------------------------------

    def test_create_booking_success(self):
        """
        TES 1: (Happy Path) Pastikan user1 bisa create booking baru.
        """
        # 1. Login sebagai user1
        self.client.login(username='user1', password='password123')
        
        # 2. Siapkan data POST
        # Pastikan kita booking jadwal yang 'is_available=True' (jadwal_senin)
        self.assertTrue(self.jadwal_senin.is_available)
        post_data = {
            'lapangan_id': self.lapangan_a.id,
            'jadwal_id': [self.jadwal_senin.id] # 'getlist' butuh format list
        }

        # 3. Kirim request POST
        response = self.client.post(self.url_create_booking, data=post_data)
        
        # 4. Cek respons JSON
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('payment_url', data) # Pastikan payment_url dikirim
        
        # 5. Cek Database (PALING PENTING)
        # Pastikan booking baru dibuat (total jadi 3)
        self.assertEqual(Booking.objects.count(), 3) 
        new_booking = Booking.objects.get(id=data['booking_id'])
        self.assertEqual(new_booking.user_id, self.profile1)
        self.assertEqual(new_booking.lapangan_id, self.lapangan_a)
        
        # 6. Cek M2M relation (jadwal)
        self.assertEqual(new_booking.jadwal.count(), 1)
        self.assertEqual(new_booking.jadwal.first(), self.jadwal_senin)

        # 7. Cek side-effect (jadwal jadi not available)
        self.jadwal_senin.refresh_from_db()
        self.assertFalse(self.jadwal_senin.is_available)

    def test_create_booking_jadwal_not_available(self):
        """
        TES 2: (Validation) Pastikan GAGAL jika jadwal.is_available=False.
        """
        # 1. Login sebagai user1
        self.client.login(username='user1', password='password123')

        # 2. Siapkan data POST, tapi pakai jadwal_selasa
        #    Lalu, kita set jadwal_selasa jadi 'not available'
        self.jadwal_selasa.is_available = False
        self.jadwal_selasa.save()
        
        post_data = {
            'lapangan_id': self.lapangan_a.id,
            'jadwal_id': [self.jadwal_selasa.id]
        }

        # 3. Kirim request POST
        response = self.client.post(self.url_create_booking, data=post_data)
        
        # 4. Cek respons JSON
        self.assertEqual(response.status_code, 400) # Sesuai view kamu
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('already booked or invalid', data['message'])
        
        # 5. Cek Database (Pastikan tidak ada booking baru yang dibuat)
        self.assertEqual(Booking.objects.count(), 2) # Harus tetap 2

    def test_create_booking_not_logged_in(self):
        """
        TES 3: (Security) Pastikan user yang belum login di-redirect.
        """
        # 1. (Jangan login)
        post_data = {
            'lapangan_id': self.lapangan_a.id,
            'jadwal_id': [self.jadwal_senin.id]
        }
        
        # 2. Kirim request POST
        response = self.client.post(self.url_create_booking, data=post_data)
        
        # 3. Cek respons (Harus 302 Redirect ke login)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url) # (Sesuaikan jika URL login-mu beda)

    def test_create_booking_wrong_method(self):
        """
        TES 4: (Logic) Pastikan GAGAL jika pakai method GET.
        """
        # 1. Login sebagai user1
        self.client.login(username='user1', password='password123')
        
        # 2. Kirim request GET
        response = self.client.get(self.url_create_booking)
        
        # 3. Cek respons JSON
        self.assertEqual(response.status_code, 405) # Sesuai view kamu
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'Invalid request method.')

    def test_show_json_as_admin(self):
                # 1. Buat TIGA user (1 admin, 1 user, 1 admin lain)
        self.user1_admin = User.objects.create_user(username='admin1', password='password123')
        self.user2_player = User.objects.create_user(username='player2', password='password123')
        self.user3_admin = User.objects.create_user(username='admin3', password='password123')

        # 2. Buat profil mereka dengan ROLE
        self.profile1_admin = UserProfile.objects.create(
            user=self.user1_admin, fullname="Admin Lapangan A", role='admin' # <-- PENTING
        )
        self.profile2_player = UserProfile.objects.create(
            user=self.user2_player, fullname="Pemain Dua", role='user' # <-- PENTING
        )
        self.profile3_admin = UserProfile.objects.create(
            user=self.user3_admin, fullname="Admin Lapangan B", role='admin'
        )

        # 3. Buat Lapangan A (milik admin1)
        self.lapangan_a1 = Lapangan.objects.create(
            name="Lapangan A", 
            price=100000,
            admin=self.user1_admin # <-- Admin adalah user1
        )
        self.jadwal_senin = Jadwal.objects.create(
            lapangan=self.lapangan_a1,
            tanggal='2025-10-27', 
            start_main='10:00:00', end_main='11:00:00'
        )
        
        # 4. Buat Lapangan B (milik admin3) - UNTUK TES ISOLASI
        self.lapangan_b = Lapangan.objects.create(
            name="Lapangan B", 
            price=50000,
            admin=self.user3_admin # <-- Admin adalah user3
        )
        self.jadwal_selasa = Jadwal.objects.create(
            lapangan=self.lapangan_b,
            tanggal='2025-10-28', 
            start_main='14:00:00', end_main='15:00:00'
        )
        
        # 5. Buat booking 'pending' oleh admin1 di lapangannya sendiri
        self.booking1_admin1 = Booking.objects.create(
            user_id=self.profile1_admin,
            lapangan_id=self.lapangan_a1,
            status_book='pending'
        )
        self.booking1_admin1.jadwal.add(self.jadwal_senin)
        
        # 6. Buat booking 'completed' oleh player2 di lapangan A
        self.booking2_player2 = Booking.objects.create(
            user_id=self.profile2_player,
            lapangan_id=self.lapangan_a1,
            status_book='completed'
        )
        # (Jadwal sengaja dikosongkan untuk tes, atau bisa ditambahkan)
        
        # 7. Buat booking 'pending' oleh player2 di lapangan B
        self.booking3_player2_lapanganB = Booking.objects.create(
            user_id=self.profile2_player,
            lapangan_id=self.lapangan_b,
            status_book='pending'
        )
        self.booking3_player2_lapanganB.jadwal.add(self.jadwal_selasa)

        # 8. Siapkan client dan URL
        self.client = Client()
        self.url_show_json = reverse('booking:show_json') 
        self.url_create_booking = reverse('booking:create_booking')


    
        """
        TES BARU 1: (Admin) Pastikan admin1 HANYA melihat booking 
        dari lapangan yang dia kelola (Lapangan A).
        """
        # 1. Login sebagai admin1
        self.client.login(username='admin1', password='password123')
        
        # 2. Panggil view show_json
        response = self.client.get(self.url_show_json)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # 3. Cek hasilnya
        # Admin1 harus melihat booking1 (miliknya) dan booking2 (milik player2),
        # karena keduanya ada di Lapangan A yang dia kelola.
        self.assertEqual(len(data), 2)
        
        # Buat set berisi ID booking yang diterima
        received_ids = {booking['id'] for booking in data}
        
        # Pastikan booking dari Lapangan A ada
        self.assertIn(str(self.booking1_admin1.id), received_ids)
        self.assertIn(str(self.booking2_player2.id), received_ids)
        
        # Pastikan booking dari Lapangan B (milik admin3) TIDAK ADA
        self.assertNotIn(str(self.booking3_player2_lapanganB.id), received_ids)

    def test_show_json_as_user(self):
        self.user1_admin = User.objects.create_user(username='admin1', password='password123')
        self.user2_player = User.objects.create_user(username='player2', password='password123')
        self.user3_admin = User.objects.create_user(username='admin3', password='password123')

        # 2. Buat profil mereka dengan ROLE
        self.profile1_admin = UserProfile.objects.create(
            user=self.user1_admin, fullname="Admin Lapangan A", role='admin' # <-- PENTING
        )
        self.profile2_player = UserProfile.objects.create(
            user=self.user2_player, fullname="Pemain Dua", role='user' # <-- PENTING
        )
        self.profile3_admin = UserProfile.objects.create(
            user=self.user3_admin, fullname="Admin Lapangan B", role='admin'
        )

        # 3. Buat Lapangan A (milik admin1)
        self.lapangan_a1 = Lapangan.objects.create(
            name="Lapangan A", 
            price=100000,
            admin=self.user1_admin # <-- Admin adalah user1
        )
        self.jadwal_senin = Jadwal.objects.create(
            lapangan=self.lapangan_a1,
            tanggal='2025-10-27', 
            start_main='10:00:00', end_main='11:00:00'
        )
        
        # 4. Buat Lapangan B (milik admin3) - UNTUK TES ISOLASI
        self.lapangan_b = Lapangan.objects.create(
            name="Lapangan B", 
            price=50000,
            admin=self.user3_admin # <-- Admin adalah user3
        )
        self.jadwal_selasa = Jadwal.objects.create(
            lapangan=self.lapangan_b,
            tanggal='2025-10-28', 
            start_main='14:00:00', end_main='15:00:00'
        )
        
        # 5. Buat booking 'pending' oleh admin1 di lapangannya sendiri
        self.booking1_admin1 = Booking.objects.create(
            user_id=self.profile1_admin,
            lapangan_id=self.lapangan_a1,
            status_book='pending'
        )
        self.booking1_admin1.jadwal.add(self.jadwal_senin)
        
        # 6. Buat booking 'completed' oleh player2 di lapangan A
        self.booking2_player2 = Booking.objects.create(
            user_id=self.profile2_player,
            lapangan_id=self.lapangan_a1,
            status_book='completed'
        )
        # (Jadwal sengaja dikosongkan untuk tes, atau bisa ditambahkan)
        
        # 7. Buat booking 'pending' oleh player2 di lapangan B
        self.booking3_player2_lapanganB = Booking.objects.create(
            user_id=self.profile2_player,
            lapangan_id=self.lapangan_b,
            status_book='pending'
        )
        self.booking3_player2_lapanganB.jadwal.add(self.jadwal_selasa)

        # 8. Siapkan client dan URL
        self.client = Client()
        self.url_show_json = reverse('booking:show_json') 
        self.url_create_booking = reverse('booking:create_booking')


    
        """
        TES BARU 2: (User) Pastikan player2 HANYA melihat booking miliknya,
        dari SEMUA lapangan yang dia booking.
        """
        # 1. Login sebagai player2
        self.client.login(username='player2', password='password123')
        
        # 2. Panggil view show_json
        response = self.client.get(self.url_show_json)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # 3. Cek hasilnya
        # Player2 harus melihat booking2 (di Lapangan A) dan booking3 (di Lapangan B)
        self.assertEqual(len(data), 2)
        
        received_ids = {booking['id'] for booking in data}
        
        # Pastikan booking miliknya ada
        self.assertIn(str(self.booking2_player2.id), received_ids)
        self.assertIn(str(self.booking3_player2_lapanganB.id), received_ids)
        
        # Pastikan booking milik admin1 TIDAK ADA
        self.assertNotIn(str(self.booking1_admin1.id), received_ids)