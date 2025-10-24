# booking/tests.py

import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, date, time

# --- ADJUST THESE IMPORTS based on your project structure ---
from authentication_user.models import UserProfile
from admin_lapangan.models import Lapangan, JadwalLapangan as Jadwal
from .models import Booking
# ---------------------------------------------------------

class BookingViewsTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        """
        Set up non-modified objects used by all test methods.
        Runs only ONCE per class. Faster for static data.
        """
        # --- Users & Profiles ---
        cls.user_admin1 = User.objects.create_user(username='admin1', password='password123')
        cls.profile_admin1 = UserProfile.objects.create(user=cls.user_admin1, fullname="Admin Satu", role='admin')

        cls.user_player2 = User.objects.create_user(username='player2', password='password123')
        cls.profile_player2 = UserProfile.objects.create(user=cls.user_player2, fullname="Pemain Dua", role='user')

        cls.user_admin3 = User.objects.create_user(username='admin3', password='password123')
        cls.profile_admin3 = UserProfile.objects.create(user=cls.user_admin3, fullname="Admin Tiga", role='admin')

        # --- Lapangan ---
        cls.lapangan_a = Lapangan.objects.create(
            name="Lapangan A (Admin1)", price=100000.00, admin_lapangan=cls.profile_admin1, location="Loc A", description="Desc A"
        )
        cls.lapangan_b = Lapangan.objects.create(
            name="Lapangan B (Admin3)", price=50000.00, admin_lapangan=cls.profile_admin3, location="Loc B", description="Desc B"
        )

        # --- Jadwal ---
        cls.today = timezone.now().date()
        cls.tomorrow = cls.today + timedelta(days=1)
        cls.day_after_tomorrow = cls.today + timedelta(days=2)
        cls.yesterday = cls.today - timedelta(days=1)
        cls.three_days_later = cls.today + timedelta(days=3)

        # Jadwal Valid for Lapangan A (will be used in various tests)
        cls.jadwal_a_today_10am = Jadwal.objects.create(lapangan=cls.lapangan_a, tanggal=cls.today, start_main=time(10, 0), end_main=time(11, 0), is_available=True)
        cls.jadwal_a_today_11am = Jadwal.objects.create(lapangan=cls.lapangan_a, tanggal=cls.today, start_main=time(11, 0), end_main=time(12, 0), is_available=True)
        cls.jadwal_a_plus2_3pm = Jadwal.objects.create(lapangan=cls.lapangan_a, tanggal=cls.day_after_tomorrow, start_main=time(15, 0), end_main=time(16, 0), is_available=True)

        # Jadwal Invalid/Edge cases for Lapangan A
        cls.jadwal_a_past = Jadwal.objects.create(lapangan=cls.lapangan_a, tanggal=cls.yesterday, start_main=time(10, 0), end_main=time(11, 0), is_available=True)
        cls.jadwal_a_future_far = Jadwal.objects.create(lapangan=cls.lapangan_a, tanggal=cls.three_days_later, start_main=time(10, 0), end_main=time(11, 0), is_available=True)
        cls.jadwal_a_not_available = Jadwal.objects.create(lapangan=cls.lapangan_a, tanggal=cls.today, start_main=time(13, 0), end_main=time(14, 0), is_available=False)

        # Jadwal for Lapangan B
        cls.jadwal_b_today_9am = Jadwal.objects.create(lapangan=cls.lapangan_b, tanggal=cls.today, start_main=time(9, 0), end_main=time(10, 0), is_available=True)

        # --- URLs ---
        # Note: URLs needing specific IDs will be created within test methods
        cls.url_show_json = reverse('booking:show_json')
        cls.url_create_booking = reverse('booking:create_booking')
        cls.url_show_booking_list = reverse('booking:show_booking_list')
        
        Jadwal.objects.filter(id=cls.jadwal_a_past.id).update(is_available=False)
        cls.jadwal_a_past.refresh_from_db() # Reload after update
    # If in setUpTestData, use cls.jadwal_a_yesterday.refresh_from_db() if needed later

        # Create a booking using this past, unavailable schedule
        cls.booking_using_past_unavailable = Booking.objects.create(
            user_id=cls.profile_player2, # Or any profile
            lapangan_id=cls.lapangan_a,
            status_book='pending'
        )
        cls.booking_using_past_unavailable.jadwal.add(cls.jadwal_a_past)


    def setUp(self):
        """
        Set up objects that might be modified by tests. Runs before EACH test.
        """
        self.client = Client()

        # --- Bookings (Create fresh for each test to avoid side-effects) ---
        # Booking pending by player2 on Lapangan A
        self.booking_p2_lapA_pending = Booking.objects.create(
            user_id=self.profile_player2, lapangan_id=self.lapangan_a, status_book='pending'
        )
        self.booking_p2_lapA_pending.jadwal.add(self.jadwal_a_today_10am)
        # Mark the booked schedule as unavailable for consistency (view does this too)
        Jadwal.objects.filter(id=self.jadwal_a_today_10am.id).update(is_available=False)


        # Booking completed by player2 on Lapangan A (use a different schedule)
        self.booking_p2_lapA_completed = Booking.objects.create(
            user_id=self.profile_player2, lapangan_id=self.lapangan_a, status_book='completed'
        )
        # Assume this was booked previously and jadwal_a_today_11am was made unavailable
        Jadwal.objects.filter(id=self.jadwal_a_today_11am.id).update(is_available=False)
        self.booking_p2_lapA_completed.jadwal.add(self.jadwal_a_today_11am)


        # Booking pending by admin1 on Lapangan B (Admin can book anywhere)
        self.booking_a1_lapB_pending = Booking.objects.create(
            user_id=self.profile_admin1, lapangan_id=self.lapangan_b, status_book='pending'
        )
        self.booking_a1_lapB_pending.jadwal.add(self.jadwal_b_today_9am)
        Jadwal.objects.filter(id=self.jadwal_b_today_9am.id).update(is_available=False)

        # --- Refresh schedules used in setup (important!) ---
        # Reload fresh copies for tests as setUp modified their availability
        self.jadwal_a_today_10am.refresh_from_db()
        self.jadwal_a_today_11am.refresh_from_db()
        self.jadwal_b_today_9am.refresh_from_db()
        # Ensure schedules not booked in setUp are available
        Jadwal.objects.filter(id=self.jadwal_a_plus2_3pm.id).update(is_available=True)
        self.jadwal_a_plus2_3pm.refresh_from_db()


    # -----------------------------------------------
    # Tests for show_create_booking
    # -----------------------------------------------
    def test_show_create_booking_renders_correctly_and_filters(self):
        """Test view renders correct template and filters jadwal."""
        url = reverse('booking:show_create_booking', kwargs={'lapangan_id': self.lapangan_a.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_book.html')
        self.assertEqual(response.context['lapangan'], self.lapangan_a)

        jadwals_in_context = response.context['jadwals']
        # Should contain ONLY jadwal_a_plus2_3pm (today's are booked or unavailable, others out of date range)
        # Note: We reset availability of jadwal_a_plus2_3pm in setUp
        self.assertEqual(jadwals_in_context.count(), 1)
        self.assertIn(self.jadwal_a_plus2_3pm, jadwals_in_context)

        # Ensure others are NOT present
        self.assertNotIn(self.jadwal_a_today_10am, jadwals_in_context) # Booked in setUp
        self.assertNotIn(self.jadwal_a_today_11am, jadwals_in_context) # Booked in setUp
        self.assertNotIn(self.jadwal_a_past, jadwals_in_context) # Wrong date
        self.assertNotIn(self.jadwal_a_future_far, jadwals_in_context) # Wrong date
        self.assertNotIn(self.jadwal_a_not_available, jadwals_in_context) # is_available=False

    def test_show_create_booking_404_invalid_lapangan(self):
        """Test view returns 404 for invalid lapangan UUID."""
        invalid_uuid = '00000000-0000-0000-0000-000000000000'
        url = reverse('booking:show_create_booking', kwargs={'lapangan_id': invalid_uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    # -----------------------------------------------
    # Tests for create_booking (API - POST)
    # -----------------------------------------------
    def test_create_booking_success(self):
        """Test successful booking creation via POST."""
        self.client.login(username='player2', password='password123')
        # Use a schedule that IS available
        self.assertTrue(self.jadwal_a_plus2_3pm.is_available)
        post_data = {
            'lapangan_id': self.lapangan_a.id,
            'jadwal_id': [self.jadwal_a_plus2_3pm.id]
        }
        response = self.client.post(self.url_create_booking, data=post_data)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('payment_url', data)
        self.assertTrue(data['payment_url'].startswith('/booking/booking_detail/'))

        # Check DB
        self.assertEqual(Booking.objects.count(), 5) # 3 from setUp + 1 new
        new_booking = Booking.objects.get(id=data['booking_id'])
        self.assertEqual(new_booking.user_id, self.profile_player2)
        self.assertEqual(new_booking.lapangan_id, self.lapangan_a)
        self.assertEqual(new_booking.status_book, 'pending')
        self.assertEqual(new_booking.jadwal.first(), self.jadwal_a_plus2_3pm)

        # Check side effect
        self.jadwal_a_plus2_3pm.refresh_from_db()
        self.assertFalse(self.jadwal_a_plus2_3pm.is_available)

    def test_create_booking_fail_jadwal_unavailable(self):
        """Test booking fails if jadwal is not available."""
        self.client.login(username='player2', password='password123')
        # Use a schedule that is NOT available (booked in setUp)
        self.assertFalse(self.jadwal_a_today_10am.is_available)
        post_data = {
            'lapangan_id': self.lapangan_a.id,
            'jadwal_id': [self.jadwal_a_today_10am.id]
        }
        response = self.client.post(self.url_create_booking, data=post_data)

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('already booked or invalid', data['message'])
        self.assertEqual(Booking.objects.count(), 4) # No new booking

    def test_create_booking_fail_no_jadwal(self):
        """Test booking fails if no valid jadwal IDs are provided."""
        self.client.login(username='player2', password='password123')
        post_data = {
            'lapangan_id': self.lapangan_a.id,
            'jadwal_id': [] # Empty list
        }
        response = self.client.post(self.url_create_booking, data=post_data)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(Booking.objects.count(), 4)

    def test_create_booking_fail_not_logged_in(self):
        """Test requires login."""
        post_data = {'lapangan_id': self.lapangan_a.id, 'jadwal_id': [self.jadwal_a_plus2_3pm.id]}
        response = self.client.post(self.url_create_booking, data=post_data)
        self.assertEqual(response.status_code, 302) # Redirects to login
        self.assertIn(reverse('authentication_user:login'), response.url)

    def test_create_booking_fail_wrong_method(self):
        """Test only accepts POST."""
        self.client.login(username='player2', password='password123')
        response = self.client.get(self.url_create_booking)
        self.assertEqual(response.status_code, 405) # Method Not Allowed

    # -----------------------------------------------
    # Tests for show_json_by_id (API - GET)
    # -----------------------------------------------
    # def test_show_json_by_id_success(self):
    #     """Test fetching specific booking details as owner."""
    #     self.client.login(username='player2', password='password123')
    #     url = reverse('booking:show_json_by_id', kwargs={'booking_id': self.booking_p2_lapA_pending.id})
    #     response = self.client.get(url)

    #     self.assertEqual(response.status_code, 200)
    #     data = response.json()
    #     self.assertEqual(data['id'], str(self.booking_p2_lapA_pending.id))
    #     self.assertEqual(data['lapangan']['name'], self.lapangan_a.name)
    #     self.assertEqual(data['user']['fullname'], self.profile_player2.fullname)
    #     self.assertEqual(data['status_book'], 'pending')
    #     self.assertEqual(len(data['jadwal']), 1)
    #     self.assertEqual(data['jadwal'][0]['start_main'], '10:00:00')

    def test_show_json_by_id_fail_not_owner(self):
        """Test user cannot fetch details of another user's booking."""
        self.client.login(username='admin1', password='password123') # Logged in as admin1
        # Try to fetch booking owned by player2
        url = reverse('booking:show_json_by_id', kwargs={'booking_id': self.booking_p2_lapA_pending.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404) # View uses get_object_or_404



    def test_show_json_by_id_fail_invalid_id(self):
        """Test 404 for invalid booking UUID."""
        self.client.login(username='player2', password='password123')
        invalid_uuid = '00000000-0000-0000-0000-000000000000'
        url = reverse('booking:show_json_by_id', kwargs={'booking_id': invalid_uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    # -----------------------------------------------
    # Tests for show_json (API - GET, List)
    # -----------------------------------------------
    def test_show_json_as_admin(self):
        """Test admin sees ONLY bookings for lapangan they manage."""
        self.client.login(username='admin1', password='password123')
        response = self.client.get(self.url_show_json)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Admin1 manages Lapangan A. Should see bookings on Lap A ONLY.
        self.assertEqual(len(data), 3)
        received_ids = {b['id'] for b in data}
        self.assertIn(str(self.booking_p2_lapA_pending.id), received_ids)
        self.assertIn(str(self.booking_p2_lapA_completed.id), received_ids)
        # Should NOT see booking on Lap B (managed by admin3)
        self.assertIn(str(self.booking_using_past_unavailable.id), received_ids)
        self.assertNotIn(str(self.booking_a1_lapB_pending.id), received_ids)

    def test_show_json_as_user(self):
        """Test regular user sees ONLY their own bookings."""
        self.client.login(username='player2', password='password123')
        response = self.client.get(self.url_show_json)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Player2 made bookings on Lap A and Lap B. Should see both.
        # Note: booking_a1_lapB_pending is owned by admin1
        self.assertEqual(len(data), 3)
        received_ids = {b['id'] for b in data}
        self.assertIn(str(self.booking_p2_lapA_pending.id), received_ids)
        self.assertIn(str(self.booking_p2_lapA_completed.id), received_ids) # Corrected this line
        # Should NOT see booking owned by admin1
        self.assertNotIn(str(self.booking_a1_lapB_pending.id), received_ids)


    def test_show_json_fail_not_logged_in(self):
        """Test requires login."""
        response = self.client.get(self.url_show_json)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('authentication_user:login'), response.url)

    # -----------------------------------------------
    # Tests for complete_booking (API - POST)
    # -----------------------------------------------
    def test_complete_booking_success(self):
        """Test owner can complete their pending booking."""
        self.client.login(username='player2', password='password123')
        url = reverse('booking:complete_booking', kwargs={'booking_id': self.booking_p2_lapA_pending.id})
        response = self.client.post(url) # POST request

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'Completed')

        # Check DB
        self.booking_p2_lapA_pending.refresh_from_db()
        self.assertEqual(self.booking_p2_lapA_pending.status_book, 'completed')

    def test_complete_booking_fail_not_owner(self):
        """Test user cannot complete another user's booking."""
        self.client.login(username='admin1', password='password123') # Logged in as admin1
        # Try to complete booking owned by player2
        url = reverse('booking:complete_booking', kwargs={'booking_id': self.booking_p2_lapA_pending.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404) # View uses get_object_or_404

    # def test_complete_booking_fail_already_completed(self):
    #     """Test cannot complete an already completed booking."""
    #     self.client.login(username='player2', password='password123')
    #     url = reverse('booking:complete_booking', kwargs={'booking_id': self.booking_p2_lapA_completed.id})
    #     response = self.client.post(url)
    #     self.assertEqual(response.status_code, 200) # View returns 200 for this case
    #     self.assertIn('already completed', response.json()['message'])

    #     # Check DB status hasn't changed
    #     self.booking_p2_lapA_completed.refresh_from_db()
    #     self.assertEqual(self.booking_p2_lapA_completed.status_book, 'completed')

    def test_complete_booking_fail_failed_status(self):
        """Test cannot complete a failed booking."""
        self.client.login(username='player2', password='password123')
        # Manually set status to failed
        self.booking_p2_lapA_pending.status_book = 'failed'
        self.booking_p2_lapA_pending.save()
        url = reverse('booking:complete_booking', kwargs={'booking_id': self.booking_p2_lapA_pending.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400) # View returns 400
        self.assertIn('expired', response.json()['message'])

    def test_complete_booking_fail_not_logged_in(self):
        """Test requires login."""
        url = reverse('booking:complete_booking', kwargs={'booking_id': self.booking_p2_lapA_pending.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('authentication_user:login'), response.url)



    # -----------------------------------------------
    # Tests for booking_detail (Renders HTML)
    # -----------------------------------------------
    def test_booking_detail_renders_as_owner(self):
        """Test owner can view the detail page."""
        self.client.login(username='player2', password='password123')
        url = reverse('booking:booking_detail', kwargs={'booking_id': self.booking_p2_lapA_pending.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'booking_detail.html')
        # Check context passed to template
        self.assertEqual(response.context['booking_id'], str(self.booking_p2_lapA_pending.id))
        self.assertEqual(response.context['lapangan_nama'], self.lapangan_a.name)

    def test_booking_detail_fail_not_owner(self):
        """Test non-owner gets 404."""
        self.client.login(username='admin1', password='password123')
        url = reverse('booking:booking_detail', kwargs={'booking_id': self.booking_p2_lapA_pending.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    # -----------------------------------------------
    # Tests for show_booking_list (Renders HTML)
    # -----------------------------------------------
    def test_show_booking_list_renders(self):
        """Test list page renders successfully for logged-in user."""
        self.client.login(username='player2', password='password123')
        response = self.client.get(self.url_show_booking_list)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'booking_list.html')

    def test_show_booking_list_fail_not_logged_in(self):
        """Test requires login."""
        response = self.client.get(self.url_show_booking_list)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('authentication_user:login'), response.url)

    # -----------------------------------------------
    # Tests for delete_booking (API - POST, Admin Only)
    # -----------------------------------------------
    def test_delete_booking_success_as_admin_reopens_future_jadwal(self):
        """Test admin can delete booking, future jadwal becomes available."""
        self.client.login(username='admin1', password='password123') # Login as admin

        # Create a booking specifically for this test with a future date
        future_date = self.today + timedelta(days=5)
        jadwal_future_test = Jadwal.objects.create(lapangan=self.lapangan_a, tanggal=future_date, start_main=time(10, 0), end_main=time(11, 0), is_available=False) # Start as unavailable
        booking_to_delete = Booking.objects.create(user_id=self.profile_player2, lapangan_id=self.lapangan_a, status_book='pending')
        booking_to_delete.jadwal.add(jadwal_future_test)

        self.assertFalse(jadwal_future_test.is_available) # Verify it's unavailable first
        self.assertEqual(Booking.objects.count(), 4) # 3 from setUp + 1 new

        url = reverse('booking:delete_booking', kwargs={'booking_id': booking_to_delete.id})
        response = self.client.post(url) # Send POST

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('Booking berhasil dihapus', data['message'])

        # Check DB
        self.assertEqual(Booking.objects.count(), 3) # Should be deleted
        with self.assertRaises(Booking.DoesNotExist):
            Booking.objects.get(id=booking_to_delete.id)

        # Check side effect: Future jadwal should be available again
        jadwal_future_test.refresh_from_db()
        self.assertTrue(jadwal_future_test.is_available)
    
    def test_delete_booking_success_as_admin_reopens_future_jadwal(self):
        self.client.login(username='admin1', password='password123')
        future_date = self.today + timedelta(days=5)
        # Use get_or_create for idempotency if tests are run weirdly
        jadwal_future_test, _ = Jadwal.objects.get_or_create(
            lapangan=self.lapangan_a, tanggal=future_date, start_main=time(10, 0),
            defaults={'end_main': time(11, 0), 'is_available': False}
        )
        # Ensure it's unavailable for this test run
        if jadwal_future_test.is_available:
            jadwal_future_test.is_available = False
            jadwal_future_test.save()

        booking_to_delete = Booking.objects.create(user_id=self.profile_player2, lapangan_id=self.lapangan_a, status_book='pending')
        booking_to_delete.jadwal.add(jadwal_future_test)

        initial_count = Booking.objects.count() # Should be 5
        self.assertFalse(jadwal_future_test.is_available)

        url = reverse('booking:delete_booking', kwargs={'booking_id': booking_to_delete.id})
        response = self.client.post(url)

        # --- MORE SPECIFIC CHECKS ---
        self.assertEqual(response.status_code, 200, f"Expected 200 OK, got {response.status_code}. Response: {response.content.decode()}")
        try:
            data = response.json()
            self.assertTrue(data.get('success'), f"Expected 'success': True in JSON response. Got: {data}")
            self.assertIn('Booking berhasil dihapus', data.get('message', ''), f"Expected success message. Got: {data}")
        except json.JSONDecodeError:
            self.fail(f"Response was not valid JSON. Status: {response.status_code}, Content: {response.content.decode()}")
        # ---------------------------

        # Check specific booking deleted first
        with self.assertRaises(Booking.DoesNotExist, msg=f"Booking {booking_to_delete.id} should have been deleted but wasn't."):
            Booking.objects.get(id=booking_to_delete.id)

        # Now check the total count
        final_count = Booking.objects.count()
        self.assertEqual(final_count, initial_count - 1, f"Expected booking count {initial_count - 1}, but got {final_count}.") # Should be 4

        # Check side effect
        jadwal_future_test.refresh_from_db()
        self.assertTrue(jadwal_future_test.is_available, "Future schedule was not reopened.")

   # booking/tests.py
    def test_delete_booking_fail_wrong_method(self):
        """Test only accepts POST."""
        self.client.login(username='admin1', password='password123')
        url = reverse('booking:delete_booking', kwargs={'booking_id': self.booking_p2_lapA_pending.id})
        response = self.client.get(url) # Send GET
        self.assertEqual(response.status_code, 405) # View explicitly checks method

    def test_delete_booking_fail_invalid_id(self):
        """Test 404 for invalid booking UUID."""
        self.client.login(username='admin1', password='password123')
        invalid_uuid = '00000000-0000-0000-0000-000000000000'
        url = reverse('booking:delete_booking', kwargs={'booking_id': invalid_uuid})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404) # View uses try/except DoesNotExist