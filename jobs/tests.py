from django.urls import reverse
from users.models import MyUser
from .models import JobListing, JobCategory, Wishlist
from django.test import Client

class WishlistTests(TestCase):
    def setUp(self):
        self.user = MyUser.objects.create_user(email='test@example.com', password='password123')
        self.category = JobCategory.objects.create(name='Tech')
        self.job = JobListing.objects.create(
            title='Software Engineer',
            company='Test Co',
            category=self.category,
            location='Remote',
            url='http://example.com'
        )
        self.client = Client()
        self.client.login(email='test@example.com', password='password123')

    def test_toggle_wishlist(self):
        # Initial check
        self.assertFalse(Wishlist.objects.filter(user=self.user, job=self.job).exists())

        # Toggle on
        response = self.client.get(reverse('toggle_wishlist', kwargs={'pk': self.job.pk}))
        self.assertTrue(Wishlist.objects.filter(user=self.user, job=self.job).exists())

        # Toggle off
        response = self.client.get(reverse('toggle_wishlist', kwargs={'pk': self.job.pk}))
        self.assertFalse(Wishlist.objects.filter(user=self.user, job=self.job).exists())

    def test_wishlist_list_view(self):
        Wishlist.objects.create(user=self.user, job=self.job)
        response = self.client.get(reverse('wishlist_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.job.title)
        self.assertContains(response, self.job.company)

    def test_unique_wishlist(self):
        Wishlist.objects.create(user=self.user, job=self.job)
        with self.assertRaises(Exception): # unique_together constraint
            Wishlist.objects.create(user=self.user, job=self.job)
