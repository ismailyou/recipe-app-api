from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
USER_TOKEN = reverse('user:token')
ME_URL = reverse('user:me')

def create_user(**params):
    """Create and return a new user instance"""
    return get_user_model().objects.create_user(**params)


class PublicUserApiTest(TestCase):
    """ Test The public features of the user API"""
    def setUp(self):
        self.client =APIClient()

    def test_create_user_successful(self):
        """Test creating user successful"""
        payload = {
            'name': 'testuser',
            'email': 'test@test.com',
            'password': 'testpassword',
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload['email'])
        self.assertTrue(user.check_password,payload['password'])
        self.assertNotIn('password', res.data)

    def test_user_eith_email_exists_error(self):
        """Test return error when email already exists"""
        payload = {
            'name': 'testuser',
            'email': 'test@test.com',
            'password': 'testpassword',
        }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """ Test an error is returned when password is too short"""
        payload = {
            'name': 'testuser',
            'email': 'test@test.com',
            'password': 'test',
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        
        # The user must not be created
        user_exists = get_user_model().objects.filter(
            email = payload['email']
        ).exists()

        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """ test generate token for valid credentialis"""
        user_details = {
            'name': 'testuser',
            'email': 'test@test.com',
            'password': 'testpassword',
        }
        create_user(**user_details)

        payload = {
            'email': user_details['email'],
            'password': user_details['password']
        }

        res = self.client.post(USER_TOKEN, payload)
        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
    
    def test_create_token_with_invalid_credentials(self):
        """ Test creating a token with invalid credentials"""

        create_user(email="email@example.com", password="goodpass")
        payload = {
            'email': "email@example.com",
            'password': "wrongpass"
        }
        res = self.client.post(USER_TOKEN, payload)
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_with_blank_password(self):
        """ Test posting a blank password return an error"""
        payload = {
            'email': "email@example.com",
            'password': ""
        }
        res = self.client.post(USER_TOKEN, payload)
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unautorized(self):
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateUserApiTest(TestCase):
    """Test API requests that require authentication"""

    def setUp(self):
        self.user = create_user(
            name='testuser',
            email='test@test.com',
            password='testpassword'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_retrieve_profile_success(self):
        """test retrieve profile for logged in user"""
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data ,{
            'name': self.user.name,
            'email': self.user.email 
        })
        self.assertNotIn('password', res.data)

    def test_post_me_not_allowed(self):
        """test post method not allowd to me endpoint"""
        res = self.client.post(ME_URL, {})
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_profile_success(self):
        """test update profile for looged in user"""

        payload = {
            'name': 'updated_testuser', 
            'password': 'updated_password',
        }
        res = self.client.patch(ME_URL, payload)
        self.user.refresh_from_db()

        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)