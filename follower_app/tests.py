from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Follower, FirebaseNotification
from .views import RemoveFollowerView
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class FollowerAppTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        self.user3 = User.objects.create_user(
            username='john_doe',
            email='john@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        
        # Create follow relationships
        self.follow1 = Follower.objects.create(
            follower=self.user1,
            following=self.user2,
            status='approved'
        )
        self.follow2 = Follower.objects.create(
            follower=self.user3,
            following=self.user2,
            status='approved'
        )

class SearchFunctionalityTestCase(APITestCase):
    def setUp(self):
        """Set up test data for search functionality"""
        self.user1 = User.objects.create_user(
            username='alice_user',
            email='alice@example.com',
            password='testpass123',
            first_name='Alice',
            last_name='Johnson'
        )
        self.user2 = User.objects.create_user(
            username='bob_developer',
            email='bob@example.com',
            password='testpass123',
            first_name='Bob',
            last_name='Smith'
        )
        self.user3 = User.objects.create_user(
            username='charlie_designer',
            email='charlie@example.com',
            password='testpass123',
            first_name='Charlie',
            last_name='Brown'
        )
        
        # Create follow relationships
        Follower.objects.create(
            follower=self.user1,
            following=self.user2,
            status='approved'
        )
        Follower.objects.create(
            follower=self.user3,
            following=self.user2,
            status='approved'
        )
        Follower.objects.create(
            follower=self.user2,
            following=self.user1,
            status='approved'
        )

    def test_search_followers_by_username(self):
        """Test searching followers by username"""
        self.client.force_authenticate(user=self.user2)
        response = self.client.get('/followers/?search=alice')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['results']), 1)
        self.assertEqual(response.data['data']['results'][0]['follower']['username'], 'alice_user')

    def test_search_followers_by_first_name(self):
        """Test searching followers by first name"""
        self.client.force_authenticate(user=self.user2)
        response = self.client.get('/followers/?search=Alice')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['results']), 1)

    def test_search_following_by_username(self):
        """Test searching following by username"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get('/following/?search=bob')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['results']), 1)
        self.assertEqual(response.data['data']['results'][0]['following']['username'], 'bob_developer')

    def test_search_pending_requests(self):
        """Test searching pending follow requests"""
        # Create a pending request
        pending_user = User.objects.create_user(
            username='pending_user',
            email='pending@example.com',
            password='testpass123'
        )
        Follower.objects.create(
            follower=pending_user,
            following=self.user2,
            status='pending'
        )
        
        self.client.force_authenticate(user=self.user2)
        response = self.client.get('/pending-requests/?search=pending')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['results']), 1)

class RemoveFollowerTestCase(APITestCase):
    def setUp(self):
        """Set up test data for remove follower functionality"""
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        
        # Create follow relationship
        self.follow_relationship = Follower.objects.create(
            follower=self.user2,
            following=self.user1,
            status='approved'
        )

    def test_remove_follower_success(self):
        """Test successfully removing a follower"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.post('/remove-follower/', {
            'follower_id': self.user2.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'Follower removed successfully')
        
        # Verify the relationship is deleted
        self.assertFalse(Follower.objects.filter(
            follower=self.user2,
            following=self.user1
        ).exists())

    def test_remove_follower_not_following(self):
        """Test removing a user who is not following"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.post('/remove-follower/', {
            'follower_id': 999  # Non-existent user
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_remove_follower_missing_follower_id(self):
        """Test removing follower without providing follower_id"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.post('/remove-follower/', {})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['message'], 'follower_id is required')

    def test_remove_follower_invalid_id_format(self):
        """Test removing follower with invalid ID format"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.post('/remove-follower/', {
            'follower_id': 'invalid_id'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_remove_follower_unauthorized(self):
        """Test removing follower without authentication"""
        response = self.client.post('/remove-follower/', {
            'follower_id': self.user2.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class NotificationSearchTestCase(APITestCase):
    def setUp(self):
        """Set up test data for notification search"""
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        
        # Create notifications
        FirebaseNotification.objects.create(
            user=self.user1,
            title='Follow Request from user2',
            body='user2 wants to follow you',
            sender=self.user2,
            notification_type='follow'
        )
        FirebaseNotification.objects.create(
            user=self.user1,
            title='System Update',
            body='Your profile has been updated',
            notification_type='system'
        )

    def test_search_notifications_by_title(self):
        """Test searching notifications by title"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get('/notifications/?search=Follow Request')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['results']), 1)

    def test_search_notifications_by_sender(self):
        """Test searching notifications by sender username"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get('/notifications/?search=user2')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['results']), 1)
