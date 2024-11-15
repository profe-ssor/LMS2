from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import MyUser
from rest_framework.authtoken.models import Token

class UserAuthTests(APITestCase):

    def setUp(self):
        self.signup_url = reverse('signup')
        self.login_url = reverse('login')
        self.user_data = {
            "email": "testuser@example.com",
            "username": "testuser",
            "password": "securepassword123"
        }

    def test_signup_user(self):
        """Test creating a new user with the signup view."""
        response = self.client.post(self.signup_url, self.user_data)
        
        # Check if user is created successfully
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)  # Token should be included in response
        self.assertEqual(response.data["user"]["email"], self.user_data["email"])
        
        # Ensure user exists in the database
        user = MyUser.objects.get(email=self.user_data["email"])
        self.assertTrue(user.check_password(self.user_data["password"]))

    def test_login_user(self):
        """Test logging in an existing user with correct credentials."""
        # First, create a user via signup
        self.client.post(self.signup_url, self.user_data)
        
        # Now, attempt to log in
        login_data = {
            "email": self.user_data["email"],
            "password": self.user_data["password"]
        }
        response = self.client.post(self.login_url, login_data)

        # Check if login is successful and token is returned
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["user"]["email"], self.user_data["email"])

    def test_login_user_invalid_password(self):
        """Test logging in with an incorrect password."""
        # Create a user first
        self.client.post(self.signup_url, self.user_data)

        # Attempt to login with the wrong password
        invalid_login_data = {
            "email": self.user_data["email"],
            "password": "wrongpassword"
        }
        response = self.client.post(self.login_url, invalid_login_data)

        # Check if login fails with the correct error message
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Invalid email or password.")

    def test_login_user_missing_email(self):
        """Test logging in without providing an email."""
        # Attempt to login without an email field
        response = self.client.post(self.login_url, {"password": "somepassword"})

        # Check if login fails with the appropriate error message
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Email and password are required.")
