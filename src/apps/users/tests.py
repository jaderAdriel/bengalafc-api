from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class UserRegistrationTest(APITestCase):
    def test_registration(self):
        url = reverse('user-list')
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().username, 'testuser')

    def test_me_returns_profile_photo_url(self):
        user = User.objects.create_user(
            username='photo-user',
            email='photo@example.com',
            password='testpassword123',
        )
        user.profile.photo.name = 'profiles/avatar.jpg'
        user.profile.save(update_fields=['photo'])
        self.client.force_authenticate(user=user)

        response = self.client.get(reverse('user-me'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['photo'],
            'http://testserver/media/profiles/avatar.jpg',
        )
        self.assertEqual(
            response.data['photo_url'],
            'http://testserver/media/profiles/avatar.jpg',
        )

    def test_me_returns_default_profile_photo_when_user_has_no_photo(self):
        user = User.objects.create_user(
            username='no-photo-user',
            email='no-photo@example.com',
            password='testpassword123',
        )
        self.client.force_authenticate(user=user)

        response = self.client.get(reverse('user-me'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['photo'],
            'http://testserver/media/profiles/default.jpg',
        )
        self.assertEqual(
            response.data['photo_url'],
            'http://testserver/media/profiles/default.jpg',
        )
