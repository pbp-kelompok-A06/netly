from unittest import mock
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model

from .views import index, serialize_lapangan, court_detail, search_courts_ajax, filter_courts

from admin_lapangan.models import Lapangan
from authentication_user.models import UserProfile

User = get_user_model()

class MockLapangan:
    def __init__(self, id, name, price, location, description, image=None):
        self.id = id
        self.name = name
        self.price = price
        self.location = location
        self.description = description
        self.image = image or ""

    def __str__(self):
        return self.name

class MockEvent:
    def __init__(self, id, name, location, description, image_url=None, start_date=None):
        self.id = id
        self.name = name
        self.location = location
        self.description = description
        self.image_url = image_url or ""
        self.start_date = start_date or "2025-12-25"

    def __str__(self):
        return self.name

class SerializeLapanganTest(TestCase):

    def test_serialization_correct(self):
        mock_lapangan = MockLapangan(
            id=1,
            name="Badminton A",
            price=50000.0,
            location="Jakarta",
            description="Lapangan Badminton Keren",
            image="/path/to/image.jpg"
        )
        expected = {
            "id": "1",
            "name": "Badminton A",
            "price": 50000.0,
            "location": "Jakarta",
            "status": "Available",
            "image": "/path/to/image.jpg",
            "description": "Lapangan Badminton Keren",
        }
        self.assertEqual(serialize_lapangan(mock_lapangan), expected)

    def test_serialization_with_none_image(self):
        mock_lapangan = MockLapangan(
            id=2,
            name="Badminton B",
            price=100000,
            location="Bandung",
            description="Lapangan Badminton",
            image=None
        )
        result = serialize_lapangan(mock_lapangan)
        self.assertEqual(result["image"], "")

class BaseViewTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        
        # Mock User Profile untuk user biasa
        self.user_profile = mock.Mock(spec=UserProfile, role="user")
        self.user = mock.Mock(spec=User, is_authenticated=True, profile=self.user_profile)

        # Mock Admin Profile
        self.admin_profile = mock.Mock(spec=UserProfile, role="admin")
        self.admin_user = mock.Mock(spec=User, is_authenticated=True, profile=self.admin_profile)

        # Mock Lapangan objects
        self.mock_lapangan_1 = MockLapangan(1, "Badminton A", 50000, "Jakarta", "Desc A")
        self.mock_lapangan_2 = MockLapangan(2, "Badminton B", 100000, "Bandung", "Desc B")
        self.mock_lapangan_3 = MockLapangan(3, "Badminton C", 75000, "Jakarta", "Desc C")
        self.mock_lapangan_list = [self.mock_lapangan_1, self.mock_lapangan_2, self.mock_lapangan_3]

        # Patch/Mock QuerySet manager Lapangan.objects
        self.mock_qs = mock.MagicMock(name="QuerySet")
        self.mock_qs.all.return_value = self.mock_lapangan_list
        # Meniru perilaku filter yang mengembalikan QuerySet baru
        self.mock_qs.filter.return_value = self.mock_qs
        self.mock_qs.order_by.return_value = self.mock_qs
        self.mock_qs.__getitem__.return_value = self.mock_lapangan_list[:1] # untuk slicing [:5], [:20]
        # Membuat iterable untuk hasil filtering
        self.mock_qs.__iter__.side_effect = lambda: iter(self.mock_lapangan_list)

        # Mock Event objects
        self.mock_event_1 = MockEvent(1, "Turnamen Badminton", "Badminton", "Event Badminton", image_url="/img/e1.jpg")
        self.mock_event_list = [self.mock_event_1]
        
        # Patch/Mock Event.objects
        self.mock_event_qs = mock.MagicMock(name="EventQuerySet")
        self.mock_event_qs.all.return_value = self.mock_event_list
        self.mock_event_qs.filter.return_value = self.mock_event_qs
        self.mock_event_qs.__getitem__.return_value = self.mock_event_list
        self.mock_event_qs.__iter__.side_effect = lambda: iter(self.mock_event_list)


@mock.patch("admin_lapangan.models.Lapangan.objects", new_callable=lambda: BaseViewTest().mock_qs)
@mock.patch("event.models.Event.objects", new_callable=lambda: BaseViewTest().mock_event_qs)
class IndexViewTest(BaseViewTest):

    def test_redirect_if_not_logged_in(self, mock_event_qs, mock_lapangan_qs):
        pass

    def test_admin_dashboard_render(self, mock_event_qs, mock_lapangan_qs):
        """Menguji admin dashboard view."""
        request = self.factory.get(reverse('index'))
        request.user = self.admin_user

        mock_lapangan_qs.filter.return_value.order_by.return_value.__getitem__.return_value = [self.mock_lapangan_1]

        response = index(request)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("dashboard.html", response.template_name)
        self.assertIn("recent_lapangan", response.context)
        self.assertIn("user_profile", response.context)
        mock_lapangan_qs.filter.assert_called_with(admin_lapangan=self.admin_profile)

    def test_user_homepage_render(self, mock_event_qs, mock_lapangan_qs):
        """Menguji user homepage (tanpa search/filter)."""
        request = self.factory.get(reverse('index'))
        request.user = self.user

        response = index(request)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("homepage/index.html", response.template_name)
        self.assertIn("court_list", response.context)
        self.assertIn("event_list", response.context)
        self.assertEqual(len(response.context["court_list"]), 3)
        self.assertEqual(len(response.context["event_list"]), 1)
        self.assertEqual(response.context["search_query"], "")

    def test_user_homepage_with_search_query(self, mock_event_qs, mock_lapangan_qs):
        """Menguji user homepage dengan query pencarian."""
        request = self.factory.get(reverse('index'), {'q': 'badminton'})
        request.user = self.user

        mock_lapangan_qs.filter.return_value = [self.mock_lapangan_1]
        mock_lapangan_qs.__iter__.side_effect = lambda: iter([self.mock_lapangan_1])

        response = index(request)

        mock_lapangan_qs.filter.assert_called_once()
        self.assertEqual(response.context["event_list"], [])
        self.assertEqual(len(response.context["court_list"]), 1)
        self.assertEqual(response.context["search_query"], "badminton")

    def test_user_homepage_with_city_filter(self, mock_event_qs, mock_lapangan_qs):
        request = self.factory.get(reverse('index'), {'city': 'Jakarta'})
        request.user = self.user

        mock_lapangan_qs.filter.return_value = [self.mock_lapangan_1, self.mock_lapangan_3]
        mock_lapangan_qs.__iter__.side_effect = lambda: iter([self.mock_lapangan_1, self.mock_lapangan_3])

        mock_event_qs.filter.return_value = [self.mock_event_1]
        mock_event_qs.__iter__.side_effect = lambda: iter([self.mock_event_1])

        response = index(request)

        self.assertEqual(mock_lapangan_qs.filter.call_count, 1) 
        mock_event_qs.filter.assert_called_once() 
        self.assertEqual(len(response.context["court_list"]), 2)
        self.assertEqual(len(response.context["event_list"]), 1)
        
        
@mock.patch("admin_lapangan.models.Lapangan.objects")
class CourtDetailViewTest(BaseViewTest):

    @mock.patch("django.shortcuts.get_object_or_404")
    def test_court_detail_renders(self, mock_get_object, mock_lapangan_qs):
        mock_get_object.return_value = self.mock_lapangan_1
        request = self.factory.get(reverse('court_detail', args=[1]))
        request.user = self.user

        response = court_detail(request, court_id=1)

        self.assertEqual(response.status_code, 200)
        self.assertIn("homepage/court_detail.html", response.template_name)
        self.assertEqual(response.context["court"].name, "Badminton A")
        mock_get_object.assert_called_once_with(Lapangan, id=1)


@mock.patch("admin_lapangan.models.Lapangan.objects", new_callable=lambda: BaseViewTest().mock_qs)
class SearchCourtsAjaxTest(BaseViewTest):

    def test_no_query_returns_all_results(self, mock_lapangan_qs):
        request = self.factory.get(reverse('search_courts_ajax'))
        
        # Mocking __getitem__ untuk [:20]
        mock_lapangan_qs.__getitem__.return_value = self.mock_lapangan_list 
        
        response = search_courts_ajax(request)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"][0]["name"], "Badminton A")
        self.assertEqual(len(response.json()["results"]), 3)
        mock_lapangan_qs.all.assert_called_once()
        self.assertFalse(mock_lapangan_qs.filter.called)

    def test_with_query_filters_results(self, mock_lapangan_qs):
        request = self.factory.get(reverse('search_courts_ajax'), {'q': 'bandung'})
        
        mock_lapangan_qs.filter.return_value = [self.mock_lapangan_2]
        mock_lapangan_qs.filter.return_value.__getitem__.return_value = [self.mock_lapangan_2]

        response = search_courts_ajax(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["results"]), 1)
        self.assertEqual(response.json()["results"][0]["name"], "Badminton B")
        mock_lapangan_qs.filter.assert_called_once()


@mock.patch("admin_lapangan.models.Lapangan.objects", new_callable=lambda: BaseViewTest().mock_qs)
class FilterCourtsTest(BaseViewTest):

    def test_filter_by_location(self, mock_lapangan_qs):
        request = self.factory.get(reverse('filter_courts'), {'location': 'Jakarta'})
        
        mock_lapangan_qs.filter.return_value = [self.mock_lapangan_1, self.mock_lapangan_3]
        mock_lapangan_qs.__iter__.side_effect = lambda: iter([self.mock_lapangan_1, self.mock_lapangan_3])

        response = filter_courts(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["results"]), 2)
        self.assertEqual(mock_lapangan_qs.filter.call_count, 1)

    def test_filter_by_min_price(self, mock_lapangan_qs):
        """Menguji filter berdasarkan harga minimum."""
        request = self.factory.get(reverse('filter_courts'), {'min_price': '100000'})
        
        mock_lapangan_qs.filter.return_value = [self.mock_lapangan_2]
        mock_lapangan_qs.__iter__.side_effect = lambda: iter([self.mock_lapangan_2])

        response = filter_courts(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["results"]), 1)
        mock_lapangan_qs.filter.assert_called_with(price__gte=100000)

    def test_filter_by_max_price_and_location(self, mock_lapangan_qs):
        """Menguji filter berdasarkan harga maksimum dan lokasi."""
        request = self.factory.get(reverse('filter_courts'), {'max_price': '75000', 'location': 'Jakarta'})
        
        mock_qs_step1 = mock.Mock()
        mock_qs_step1.filter.return_value = [self.mock_lapangan_1]
        mock_qs_step1.__iter__.side_effect = lambda: iter([self.mock_lapangan_1])
        
        mock_lapangan_qs.all.return_value = mock_qs_step1
        
        mock_lapangan_qs.all.return_value = mock.MagicMock()
        mock_lapangan_qs.all.return_value.filter.return_value = mock.MagicMock()
        
        response = filter_courts(request)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_lapangan_qs.all.return_value.filter.call_count, 2)
        
    def test_invalid_price_is_ignored(self, mock_lapangan_qs):
        request = self.factory.get(reverse('filter_courts'), {'min_price': 'invalid', 'location': 'Jakarta'})
        
        mock_lapangan_qs.all.reset_mock()
        mock_lapangan_qs.filter.reset_mock()
        
        mock_lapangan_qs.all.return_value = mock.MagicMock()
        mock_lapangan_qs.all.return_value.filter.return_value = [self.mock_lapangan_1]
        mock_lapangan_qs.all.return_value.filter.return_value.__iter__.side_effect = lambda: iter([self.mock_lapangan_1])

        response = filter_courts(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_lapangan_qs.all.return_value.filter.call_count, 1)