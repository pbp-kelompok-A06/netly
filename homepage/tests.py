import uuid
from datetime import date, time, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from authentication_user.models import UserProfile
from admin_lapangan.models import Lapangan, JadwalLapangan
from event.models import Event

User = get_user_model()

class HomepageBaseTest(TestCase):

    def setUp(self):
        self.client = Client()


        self.admin_user = User.objects.create_user(username='testadmin', password='password123')
        self.admin_profile = UserProfile.objects.create(
            user=self.admin_user, fullname='Admin Lapangan Keren', role='admin', location='Jakarta'
        )
        self.admin_user.refresh_from_db()


        self.regular_user = User.objects.create_user(username='testplayer', password='password123')
        self.regular_profile = UserProfile.objects.create(
            user=self.regular_user, fullname='Pemain Handal', role='user', location='Bandung'
        )
        self.regular_user.refresh_from_db()


        self.lapangan_futsal = Lapangan.objects.create(
            admin_lapangan=self.admin_profile,
            name="Lapangan Futsal Jakarta Pusat",
            location="Jakarta",
            description="Lapangan futsal indoor standar internasional.",
            price=150000.00
        )
        self.lapangan_badminton = Lapangan.objects.create(
            admin_lapangan=self.admin_profile,
            name="Arena Badminton Bandung",
            location="Bandung",
            description="Arena badminton dengan 4 court.",
            price=75000.00
        )

        self.jadwal_futsal = JadwalLapangan.objects.create(
            lapangan=self.lapangan_futsal,
            tanggal=date.today() + timedelta(days=5),
            start_main=time(19, 0),
            end_main=time(20, 0)
        )


        self.event_jakarta = Event.objects.create(
            admin=self.admin_profile,
            name="Turnamen Futsal Jakarta",
            description="Turnamen futsal antar RW.",
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=11),
            location="Jakarta",
            max_participants=32
        )

class IndexViewTest(HomepageBaseTest):

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(reverse('homepage:homepage'))
        self.assertRedirects(response, f"{reverse('authentication_user:login')}?next={reverse('homepage:homepage')}")


    def test_user_renders_homepage_template_no_filters(self):
        self.client.login(username='testplayer', password='password123')
        response = self.client.get(reverse('homepage:homepage'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'homepage/index.html')
        self.assertEqual(len(response.context['court_list']), 2)
        self.assertEqual(len(response.context['event_list']), 1)
        self.assertEqual(response.context['search_query'], "")

    def test_homepage_with_search_query_q(self):
        self.client.login(username='testplayer', password='password123')
        response = self.client.get(reverse('homepage:homepage'), {'q': 'Futsal'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['court_list']), 1)
        self.assertEqual(response.context['court_list'][0]['name'], "Lapangan Futsal Jakarta Pusat")
        self.assertEqual(len(response.context['event_list']), 0)
        self.assertEqual(response.context['search_query'], "Futsal")

    def test_homepage_with_city_filter(self):
        self.client.login(username='testplayer', password='password123')
        response = self.client.get(reverse('homepage:homepage'), {'city': 'Jakarta'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['court_list']), 1)
        self.assertEqual(len(response.context['event_list']), 1)
        self.assertEqual(response.context['court_list'][0]['location'], 'Jakarta')
        self.assertEqual(response.context['event_list'][0]['location'], 'Jakarta')


class CourtDetailViewTest(HomepageBaseTest):
    def test_renders_correctly_for_valid_court(self):
        url = reverse('homepage:court-detail', args=[self.lapangan_futsal.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'homepage/court_detail.html')
        self.assertEqual(response.context['court'], self.lapangan_futsal)
        self.assertContains(response, "Lapangan Futsal Jakarta Pusat")

    def test_returns_404_for_invalid_court_uuid(self):
        invalid_uuid = uuid.uuid4()
        url = reverse('homepage:court-detail', args=[invalid_uuid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class AjaxViewsTest(HomepageBaseTest):
    def test_search_ajax_no_query(self):
        response = self.client.get(reverse('homepage:search-courts-ajax'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'application/json')
        self.assertEqual(len(response.json()['results']), 2)

    def test_search_ajax_with_query(self):
        response = self.client.get(reverse('homepage:search-courts-ajax'), {'q': 'Bandung'})
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'Arena Badminton Bandung')

    def test_filter_ajax_by_location(self):
        response = self.client.get(reverse('homepage:filter-courts'), {'location': 'Jakarta'})
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['location'], 'Jakarta')

    def test_filter_ajax_by_min_price(self):
        response = self.client.get(reverse('homepage:filter-courts'), {'min_price': '100000'})
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['price'], 150000.00)

    def test_filter_ajax_by_max_price(self):
        response = self.client.get(reverse('homepage:filter-courts'), {'max_price': '80000'})
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['price'], 75000.00)

    def test_filter_ajax_ignores_invalid_price(self):
        response = self.client.get(reverse('homepage:filter-courts'), {'min_price': 'abc', 'location': 'Jakarta'})
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['location'], 'Jakarta')

    def test_filter_ajax_with_all_params(self):
        params = {
            'q': 'Futsal',
            'location': 'Jakarta',
            'min_price': '100000',
            'max_price': '200000'
        }
        response = self.client.get(reverse('homepage:filter-courts'), params)
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'Lapangan Futsal Jakarta Pusat')