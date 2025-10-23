from django.test import TestCase
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

# -----------------------------------------------------------------
# PENTING: Perbaiki path import ini agar sesuai dengan proyekmu!
# -----------------------------------------------------------------
# Asumsi UserProfile ada di app 'authentication_user'
from authentication_user.models import UserProfile
# Asumsi Lapangan & Jadwal ada di app 'main' (atau app lain)
from admin_lapangan.models import Lapangan
from admin_lapangan.models import JadwalLapangan as Jadwal
# Import model Booking dari app ini
from .models import Booking
# -----------------------------------------------------------------


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
            admin=self.user1  # <--- TAMBAHKAN INI
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