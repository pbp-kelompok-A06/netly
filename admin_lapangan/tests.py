from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from authentication_user.models import UserProfile
from admin_lapangan.models import Lapangan, JadwalLapangan
from datetime import date, time, timedelta
import json
from decimal import Decimal

# Create your tests here.
class AdminLapanganTestCase(TestCase):
    """Base test case dengan setup untuk admin dan user"""
    
    def setUp(self):
        """Setup data untuk testing"""
        self.client = Client()
        
        # Buat admin user
        self.admin_user = User.objects.create_user(
            username='admin_test',
            password='testpass123'
        )
        self.admin_profile = UserProfile.objects.create(
            user=self.admin_user,
            fullname='Admin Test',
            role='admin'
        )
        
        # Buat regular user
        self.regular_user = User.objects.create_user(
            username='user_test',
            password='testpass123'
        )
        self.regular_profile = UserProfile.objects.create(
            user=self.regular_user,
            fullname='User Test',
            role='user'
        )
        
        # Buat admin user lain
        self.other_admin_user = User.objects.create_user(
            username='other_admin',
            password='testpass123'
        )
        self.other_admin_profile = UserProfile.objects.create(
            user=self.other_admin_user,
            fullname='Other Admin',
            role='admin'
        )
        
        # Buat lapangan untuk testing
        self.lapangan1 = Lapangan.objects.create(
            admin_lapangan=self.admin_profile,
            name='Lapangan A',
            location='Jakarta Selatan',
            description='Lapangan bagus',
            price=Decimal('100000.00'),
            image='https://example.com/image1.jpg'
        )
        
        self.lapangan2 = Lapangan.objects.create(
            admin_lapangan=self.admin_profile,
            name='Lapangan B',
            location='Jakarta Pusat',
            description='Lapangan nyaman',
            price=Decimal('150000.00'),
            image='https://example.com/image2.jpg'
        )
        
        # Buat jadwal untuk testing
        tomorrow = date.today() + timedelta(days=1)
        self.jadwal1 = JadwalLapangan.objects.create(
            lapangan=self.lapangan1,
            tanggal=tomorrow,
            start_main=time(8, 0),
            end_main=time(10, 0),
            is_available=True
        )
        
        self.jadwal2 = JadwalLapangan.objects.create(
            lapangan=self.lapangan1,
            tanggal=tomorrow,
            start_main=time(10, 0),
            end_main=time(12, 0),
            is_available=True
        )

class AdminDashboardTest(AdminLapanganTestCase):
    """Test untuk admin_dashboard view"""
    
    def test_dashboard_access_as_admin(self):
        """Test admin bisa akses dashboard"""
        self.client.login(username='admin_test', password='testpass123')
        response = self.client.get(reverse('admin_lapangan:dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')
        self.assertIn('recent_lapangan', response.context)
    
    def test_dashboard_access_as_regular_user(self):
        """Test user biasa tidak bisa akses dashboard"""
        self.client.login(username='user_test', password='testpass123')
        response = self.client.get(reverse('admin_lapangan:dashboard'))
        
        self.assertEqual(response.status_code, 403)
    
    def test_dashboard_access_without_login(self):
        """Test tanpa login redirect ke login page"""
        response = self.client.get(reverse('admin_lapangan:dashboard'))
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    

class LapanganListTest(AdminLapanganTestCase):
    """Test untuk show_lapangan_list view"""
    
    def test_lapangan_list_access_as_admin(self):
        """Test admin bisa akses list lapangan"""
        self.client.login(username='admin_test', password='testpass123')
        response = self.client.get(reverse('admin_lapangan:lapangan_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'lapangan_list.html')
    
    def test_lapangan_list_shows_only_own_lapangan(self):
        """Test admin hanya melihat lapangannya sendiri"""
        self.client.login(username='admin_test', password='testpass123')
        response = self.client.get(reverse('admin_lapangan:lapangan_list'))
        
        lapangans = response.context['lapangans']
        self.assertEqual(lapangans.paginator.count, 2)
        for lapangan in lapangans:
            self.assertEqual(lapangan.admin_lapangan, self.admin_profile)
    
    def test_lapangan_list_search_by_name(self):
        """Test search lapangan berdasarkan nama"""
        self.client.login(username='admin_test', password='testpass123')
        response = self.client.get(
            reverse('admin_lapangan:lapangan_list'),
            {'search': 'Lapangan A'}
        )
        
        lapangans = response.context['lapangans']
        self.assertEqual(lapangans.paginator.count, 1)
        self.assertEqual(lapangans[0].name, 'Lapangan A')
    
    def test_lapangan_list_search_by_location(self):
        """Test search lapangan berdasarkan lokasi"""
        self.client.login(username='admin_test', password='testpass123')
        response = self.client.get(
            reverse('admin_lapangan:lapangan_list'),
            {'search': 'Selatan'}
        )
        
        lapangans = response.context['lapangans']
        self.assertEqual(lapangans.paginator.count, 1)
        self.assertEqual(lapangans[0].location, 'Jakarta Selatan')

class LapanganDetailTest(AdminLapanganTestCase):
    """Test untuk lapangan_detail view"""
    
    def test_lapangan_detail_access_as_owner(self):
        """Test admin bisa akses detail lapangan miliknya"""
        self.client.login(username='admin_test', password='testpass123')
        response = self.client.get(
            reverse('admin_lapangan:lapangan_detail', args=[self.lapangan1.id])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'lapangan_detail.html')
        self.assertEqual(response.context['lapangan'], self.lapangan1)
    
    def test_lapangan_detail_access_as_other_admin(self):
        """Test admin lain tidak bisa akses detail lapangan"""
        self.client.login(username='other_admin', password='testpass123')
        response = self.client.get(
            reverse('admin_lapangan:lapangan_detail', args=[self.lapangan1.id])
        )
        
        self.assertEqual(response.status_code, 404)
    
    def test_lapangan_detail_shows_jadwal(self):
        """Test detail lapangan menampilkan jadwal"""
        self.client.login(username='admin_test', password='testpass123')
        response = self.client.get(
            reverse('admin_lapangan:lapangan_detail', args=[self.lapangan1.id])
        )
        
        jadwals = response.context['jadwals']
        self.assertEqual(len(jadwals), 2)

class CreateLapanganAjaxTest(AdminLapanganTestCase):
    """Test untuk create_lapangan_ajax view"""
    
    def test_create_lapangan_success(self):
        """Test create lapangan berhasil"""
        self.client.login(username='admin_test', password='testpass123')
        
        data = {
            'name': 'Lapangan C',
            'location': 'Jakarta Barat',
            'description': 'Lapangan baru',
            'price': '120000',
            'image': 'https://example.com/image3.jpg'
        }
        
        response = self.client.post(
            reverse('admin_lapangan:create_lapangan_ajax'),
            data=data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        
        # Verify lapangan created
        self.assertTrue(
            Lapangan.objects.filter(name='Lapangan C').exists()
        )
    
    def test_create_lapangan_invalid_price(self):
        """Test create lapangan dengan harga negatif"""
        self.client.login(username='admin_test', password='testpass123')
        
        data = {
            'name': 'Lapangan Invalid',
            'location': 'Jakarta',
            'description': 'Test',
            'price': '-1000',
            'image': ''
        }
        
        response = self.client.post(
            reverse('admin_lapangan:create_lapangan_ajax'),
            data=data
        )
        
        self.assertEqual(response.status_code, 400)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'error')
    
    def test_create_lapangan_as_regular_user(self):
        """Test user biasa tidak bisa create lapangan"""
        self.client.login(username='user_test', password='testpass123')
        
        data = {
            'name': 'Lapangan Test',
            'location': 'Jakarta',
            'description': 'Test',
            'price': '100000'
        }
        
        response = self.client.post(
            reverse('admin_lapangan:create_lapangan_ajax'),
            data=data
        )
        
        self.assertEqual(response.status_code, 403)

class GetLapanganJsonTest(AdminLapanganTestCase):
    """Test untuk get_lapangan_json view"""
    
    def test_get_lapangan_json_success(self):
        """Test get lapangan data sebagai JSON"""
        self.client.login(username='admin_test', password='testpass123')
        response = self.client.get(
            reverse('admin_lapangan:get_lapangan_json', args=[self.lapangan1.id])
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['data']['name'], 'Lapangan A')
        self.assertEqual(result['data']['location'], 'Jakarta Selatan')
    
    def test_get_lapangan_json_not_owner(self):
        """Test get lapangan JSON bukan miliknya"""
        self.client.login(username='other_admin', password='testpass123')
        response = self.client.get(
            reverse('admin_lapangan:get_lapangan_json', args=[self.lapangan1.id])
        )
        
        self.assertEqual(response.status_code, 404)

class EditLapanganAjaxTest(AdminLapanganTestCase):
    """Test untuk edit_lapangan_ajax view"""
    
    def test_edit_lapangan_success(self):
        """Test edit lapangan berhasil"""
        self.client.login(username='admin_test', password='testpass123')
        
        data = {
            'name': 'Lapangan A Updated',
            'location': 'Jakarta Timur',
            'description': 'Updated description',
            'price': '200000',
            'image': 'https://example.com/new-image.jpg'
        }
        
        response = self.client.post(
            reverse('admin_lapangan:edit_lapangan_ajax', args=[self.lapangan1.id]),
            data=data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        
        # Verify changes
        self.lapangan1.refresh_from_db()
        self.assertEqual(self.lapangan1.name, 'Lapangan A Updated')
        self.assertEqual(self.lapangan1.price, Decimal('200000.00'))
    
    def test_edit_lapangan_not_owner(self):
        """Test edit lapangan bukan miliknya"""
        self.client.login(username='other_admin', password='testpass123')
        
        data = {
            'name': 'Hacked Name',
            'location': 'Hacked Location',
            'description': 'Hacked',
            'price': '1000000'
        }
        
        response = self.client.post(
            reverse('admin_lapangan:edit_lapangan_ajax', args=[self.lapangan1.id]),
            data=data
        )
        
        self.assertEqual(response.status_code, 404)

class DeleteLapanganAjaxTest(AdminLapanganTestCase):
    """Test untuk delete_lapangan_ajax view"""
    
    def test_delete_lapangan_success(self):
        """Test delete lapangan berhasil"""
        self.client.login(username='admin_test', password='testpass123')
        lapangan_id = self.lapangan1.id
        
        response = self.client.post(
            reverse('admin_lapangan:delete_lapangan_ajax', args=[lapangan_id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        
        # Verify deletion
        self.assertFalse(Lapangan.objects.filter(id=lapangan_id).exists())
    
    def test_delete_lapangan_not_owner(self):
        """Test delete lapangan bukan miliknya"""
        self.client.login(username='other_admin', password='testpass123')
        
        response = self.client.post(
            reverse('admin_lapangan:delete_lapangan_ajax', args=[self.lapangan1.id])
        )
        
        self.assertEqual(response.status_code, 404)
        # Verify not deleted
        self.assertTrue(Lapangan.objects.filter(id=self.lapangan1.id).exists())

class JadwalListTest(AdminLapanganTestCase):
    """Test untuk show_jadwal_list view"""
    
    def test_jadwal_list_access_as_owner(self):
        """Test admin bisa akses list jadwal lapangannya"""
        self.client.login(username='admin_test', password='testpass123')
        response = self.client.get(
            reverse('admin_lapangan:jadwal_list', args=[self.lapangan1.id])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'jadwal_list.html')
        self.assertEqual(response.context['lapangan'], self.lapangan1)
    
    def test_jadwal_list_access_as_other_admin(self):
        """Test admin lain tidak bisa akses list jadwal"""
        self.client.login(username='other_admin', password='testpass123')
        response = self.client.get(
            reverse('admin_lapangan:jadwal_list', args=[self.lapangan1.id])
        )
        
        self.assertEqual(response.status_code, 404)

class CreateJadwalAjaxTest(AdminLapanganTestCase):
    """Test untuk create_jadwal_ajax view"""
    
    def test_create_jadwal_success(self):
        """Test create jadwal berhasil"""
        self.client.login(username='admin_test', password='testpass123')
        
        future_date = date.today() + timedelta(days=2)
        data = {
            'tanggal': future_date.strftime('%Y-%m-%d'),
            'start_main': '14:00',
            'end_main': '16:00',
            'is_available': 'true'
        }
        
        response = self.client.post(
            reverse('admin_lapangan:create_jadwal_ajax', args=[self.lapangan1.id]),
            data=data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        
        # Verify jadwal created
        self.assertTrue(
            JadwalLapangan.objects.filter(
                lapangan=self.lapangan1,
                tanggal=future_date
            ).exists()
        )
    
    def test_create_jadwal_past_date(self):
        """Test create jadwal dengan tanggal di masa lalu"""
        self.client.login(username='admin_test', password='testpass123')
        
        past_date = date.today() - timedelta(days=1)
        data = {
            'tanggal': past_date.strftime('%Y-%m-%d'),
            'start_main': '14:00',
            'end_main': '16:00',
            'is_available': 'true'
        }
        
        response = self.client.post(
            reverse('admin_lapangan:create_jadwal_ajax', args=[self.lapangan1.id]),
            data=data
        )
        
        self.assertEqual(response.status_code, 400)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'error')
    
    def test_create_jadwal_invalid_time(self):
        """Test create jadwal dengan waktu mulai >= waktu selesai"""
        self.client.login(username='admin_test', password='testpass123')
        
        future_date = date.today() + timedelta(days=2)
        data = {
            'tanggal': future_date.strftime('%Y-%m-%d'),
            'start_main': '16:00',
            'end_main': '14:00',  # End before start
            'is_available': 'true'
        }
        
        response = self.client.post(
            reverse('admin_lapangan:create_jadwal_ajax', args=[self.lapangan1.id]),
            data=data
        )
        
        self.assertEqual(response.status_code, 400)

class GetJadwalJsonTest(AdminLapanganTestCase):
    """Test untuk get_jadwal_json view"""
    
    def test_get_jadwal_json_success(self):
        """Test get jadwal data sebagai JSON"""
        self.client.login(username='admin_test', password='testpass123')
        response = self.client.get(
            reverse('admin_lapangan:get_jadwal_json', args=[self.jadwal1.id])
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        self.assertIn('tanggal', result['data'])
        self.assertIn('start_main', result['data'])

class EditJadwalAjaxTest(AdminLapanganTestCase):
    """Test untuk edit_jadwal_ajax view"""
    
    def test_edit_jadwal_success(self):
        """Test edit jadwal berhasil"""
        self.client.login(username='admin_test', password='testpass123')
        
        future_date = date.today() + timedelta(days=3)
        data = {
            'tanggal': future_date.strftime('%Y-%m-%d'),
            'start_main': '13:00',
            'end_main': '15:00',
            'is_available': 'false'
        }
        
        response = self.client.post(
            reverse('admin_lapangan:edit_jadwal_ajax', args=[self.jadwal1.id]),
            data=data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        
        # Verify changes
        self.jadwal1.refresh_from_db()
        self.assertEqual(self.jadwal1.tanggal, future_date)
        self.assertFalse(self.jadwal1.is_available)

class DeleteJadwalAjaxTest(AdminLapanganTestCase):
    """Test untuk delete_jadwal_ajax view"""
    
    def test_delete_jadwal_success(self):
        """Test delete jadwal berhasil"""
        self.client.login(username='admin_test', password='testpass123')
        jadwal_id = self.jadwal1.id
        
        response = self.client.post(
            reverse('admin_lapangan:delete_jadwal_ajax', args=[jadwal_id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        
        # Verify deletion
        self.assertFalse(JadwalLapangan.objects.filter(id=jadwal_id).exists())

class FetchLapanganListAjaxTest(AdminLapanganTestCase):
    """Test untuk fetch_lapangan_list_ajax view"""
    
    def test_fetch_lapangan_list_success(self):
        """Test fetch list lapangan via AJAX"""
        self.client.login(username='admin_test', password='testpass123')
        response = self.client.get(
            reverse('admin_lapangan:fetch_lapangan_list_ajax')
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['data']), 2)
    
    def test_fetch_lapangan_list_with_search(self):
        """Test fetch list lapangan dengan search"""
        self.client.login(username='admin_test', password='testpass123')
        response = self.client.get(
            reverse('admin_lapangan:fetch_lapangan_list_ajax'),
            {'search': 'Lapangan B'}
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(len(result['data']), 1)
        self.assertEqual(result['data'][0]['name'], 'Lapangan B')

class FetchJadwalListAjaxTest(AdminLapanganTestCase):
    """Test untuk fetch_jadwal_list_ajax view"""
    
    def test_fetch_jadwal_list_success(self):
        """Test fetch list jadwal via AJAX"""
        self.client.login(username='admin_test', password='testpass123')
        response = self.client.get(
            reverse('admin_lapangan:fetch_jadwal_list_ajax', args=[self.lapangan1.id])
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['data']), 2)
    
    def test_fetch_jadwal_list_not_owner(self):
        """Test fetch jadwal list bukan miliknya"""
        self.client.login(username='other_admin', password='testpass123')
        response = self.client.get(
            reverse('admin_lapangan:fetch_jadwal_list_ajax', args=[self.lapangan1.id])
        )
        
        self.assertEqual(response.status_code, 404)

class LapanganModelTest(TestCase):
    """Test untuk Lapangan model"""
    
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin_model_test',
            password='testpass123'
        )
        self.admin_profile = UserProfile.objects.create(
            user=self.admin_user,
            fullname='Admin Model Test',
            role='admin'
        )
    
    def test_lapangan_creation(self):
        """Test pembuatan lapangan"""
        lapangan = Lapangan.objects.create(
            admin_lapangan=self.admin_profile,
            name='Test Lapangan',
            location='Test Location',
            description='Test Description',
            price=Decimal('100000.00')
        )
        
        self.assertIsNotNone(lapangan.id)
        self.assertEqual(str(lapangan), 'Test Lapangan')
class JadwalLapanganModelTest(TestCase):
    """Test untuk JadwalLapangan model"""
    
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin_jadwal_test',
            password='testpass123'
        )
        self.admin_profile = UserProfile.objects.create(
            user=self.admin_user,
            fullname='Admin Jadwal Test',
            role='admin'
        )
        
        self.lapangan = Lapangan.objects.create(
            admin_lapangan=self.admin_profile,
            name='Test Lapangan',
            location='Test Location',
            description='Test Description',
            price=Decimal('100000.00')
        )
    
    def test_jadwal_creation(self):
        """Test pembuatan jadwal"""
        tomorrow = date.today() + timedelta(days=1)
        jadwal = JadwalLapangan.objects.create(
            lapangan=self.lapangan,
            tanggal=tomorrow,
            start_main=time(8, 0),
            end_main=time(10, 0),
            is_available=True
        )
        
        self.assertIsNotNone(jadwal.id)
        self.assertTrue(jadwal.is_available)
    
    def test_jadwal_unique_constraint(self):
        """Test unique constraint pada jadwal"""
        tomorrow = date.today() + timedelta(days=1)
        
        JadwalLapangan.objects.create(
            lapangan=self.lapangan,
            tanggal=tomorrow,
            start_main=time(8, 0),
            end_main=time(10, 0)
        )
        
        # Mencoba buat jadwal duplicate
        with self.assertRaises(Exception):
            JadwalLapangan.objects.create(
                lapangan=self.lapangan,
                tanggal=tomorrow,
                start_main=time(8, 0),  # Same time
                end_main=time(10, 0)
            )