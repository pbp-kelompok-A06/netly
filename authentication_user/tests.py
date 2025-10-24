import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import UserProfile

class AuthViewsTest(TestCase):
    """
    Kelas tes untuk semua view yang berhubungan dengan autentikasi.
    """

    def setUp(self):
        """
        Menyiapkan data yang dibutuhkan untuk tes, seperti client dan user yang sudah ada.
        """
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.profile = UserProfile.objects.create(user=self.user, fullname='Test User Fullname')
        
        # URL yang akan sering digunakan
        self.register_url = reverse('authentication_user:register')
        self.login_url = reverse('authentication_user:login')
        self.logout_url = reverse('authentication_user:logout')
        self.register_ajax_url = reverse('authentication_user:register_ajax')
        self.login_ajax_url = reverse('authentication_user:login_ajax')
        self.make_admin_url = reverse('authentication_user:make_admin')
        self.homepage_url = reverse('homepage:homepage') 

    # === Tes untuk View Statis (GET requests) ===

    def test_register_view_for_anonymous_user(self):
        """Uji bahwa pengguna anonim bisa mengakses halaman register."""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')

    def test_register_view_for_logged_in_user(self):
        """Uji bahwa pengguna yang sudah login akan diarahkan dari halaman register."""
        self.client.login(username='testuser', password='password123')
        response = self.client.get(self.register_url)
        self.assertRedirects(response, self.homepage_url)

    def test_login_view_for_anonymous_user(self):
        """Uji bahwa pengguna anonim bisa mengakses halaman login."""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')

    def test_login_view_for_logged_in_user(self):
        """Uji bahwa pengguna yang sudah login akan diarahkan dari halaman login."""
        self.client.login(username='testuser', password='password123')
        response = self.client.get(self.login_url)
        self.assertRedirects(response, self.homepage_url)

    # === Tes untuk Logout View ===
    
    def test_logout_view(self):
        """Uji fungsionalitas logout."""
        self.client.login(username='testuser', password='password123')
        # Pastikan user sudah login
        self.assertIn('_auth_user_id', self.client.session)
        
        response = self.client.get(self.logout_url)
        # Pastikan user diarahkan ke halaman login setelah logout
        self.assertRedirects(response, self.login_url)
        # Pastikan session user sudah kosong
        self.assertNotIn('_auth_user_id', self.client.session)

    # === Tes untuk Register AJAX (POST requests) ===

    def test_register_ajax_success(self):
        """Uji registrasi berhasil melalui AJAX."""
        data = {
            'username': 'newuser',
            'password1': 'newpassword123',
            'password2': 'newpassword123',
            'full_name': 'New User Fullname',
            'location': 'Jakarta',
            'profile_picture': 'http://example.com/pic.jpg'
        }
        response = self.client.post(
            self.register_ajax_url, 
            data=json.dumps(data), 
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        
        # Cek apakah user dan profile benar-benar dibuat di database
        self.assertTrue(User.objects.filter(username='newuser').exists())
        self.assertTrue(UserProfile.objects.filter(fullname='New User Fullname').exists())
        
        # Cek apakah user otomatis login setelah registrasi
        self.assertIn('_auth_user_id', self.client.session)

    def test_register_ajax_password_mismatch(self):
        """Uji registrasi gagal karena password tidak cocok."""
        data = {'username': 'user2', 'password1': 'pass1', 'password2': 'pass2', 'full_name': 'Mismatch User'}
        response = self.client.post(self.register_ajax_url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['message'], 'Passwords tidak cocok.')

    def test_register_ajax_username_exists(self):
        """Uji registrasi gagal karena username sudah dipakai."""
        data = {'username': 'testuser', 'password1': 'pass', 'password2': 'pass', 'full_name': 'Existing User'}
        response = self.client.post(self.register_ajax_url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['message'], 'Username ini sudah dipakai.')

    def test_register_ajax_missing_fields(self):
        """Uji registrasi gagal karena ada field yang kosong."""
        data = {'username': 'user3', 'password1': 'pass'} # full_name dan password2 kosong
        response = self.client.post(self.register_ajax_url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['message'], 'Semua field wajib diisi.')
        
    def test_register_ajax_invalid_json(self):
        """Uji request dengan format JSON yang salah."""
        response = self.client.post(self.register_ajax_url, data='bukan json', content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['message'], 'Format data tidak valid.')

    # === Tes untuk Login AJAX (POST requests) ===

    def test_login_ajax_success(self):
        """Uji login berhasil melalui AJAX."""
        data = {'username': 'testuser', 'password': 'password123'}
        response = self.client.post(self.login_ajax_url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        self.assertIn('_auth_user_id', self.client.session)

    def test_login_ajax_wrong_password(self):
        """Uji login gagal karena password salah."""
        data = {'username': 'testuser', 'password': 'wrongpassword'}
        response = self.client.post(self.login_ajax_url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['message'], 'Username atau password salah.')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_ajax_missing_fields(self):
        """Uji login gagal karena data tidak lengkap."""
        data = {'username': 'testuser'} # password kosong
        response = self.client.post(self.login_ajax_url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['message'], 'Username dan password wajib diisi.')

    # === Tes untuk Fungsi Utilitas `make_admin` ===
    
    def test_make_admin_creates_admins(self):
        """Uji bahwa `make_admin` berhasil membuat admin baru."""
        # Pastikan belum ada admin
        self.assertFalse(User.objects.filter(username='admin_bagus').exists())
        
        response = self.client.get(self.make_admin_url)
        self.assertEqual(response.status_code, 200)
        
        # Cek apakah 3 admin berhasil dibuat
        self.assertEqual(User.objects.filter(profile__role='admin').count(), 3)
        self.assertTrue(User.objects.filter(username='admin_bagus').exists())
        admin_dewa_profile = UserProfile.objects.get(user__username='admin_dewa')
        self.assertEqual(admin_dewa_profile.role, 'admin')

    def test_make_admin_does_not_create_duplicates(self):
        """Uji bahwa `make_admin` tidak membuat admin duplikat jika dijalankan lagi."""
        # Jalankan pertama kali
        self.client.get(self.make_admin_url)
        self.assertEqual(UserProfile.objects.filter(role='admin').count(), 3)
        
        # Jalankan kedua kali
        self.client.get(self.make_admin_url)
        # Jumlah admin harus tetap sama
        self.assertEqual(UserProfile.objects.filter(role='admin').count(), 3)