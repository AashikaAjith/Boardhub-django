from django.core import mail
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase
import re

class PasswordResetMailTests(TestCase):
    def setUp(self):
        # Create a test user
        User.objects.create_user(username='john', email='john@doe.com', password='123')
        # Trigger password reset
        self.response = self.client.post(reverse('password_reset'), {'email': 'john@doe.com'})
        # Get the first email sent
        self.email = mail.outbox[0]

    def test_email_subject(self):
        """Check the email subject"""
        self.assertEqual('[BoardHub] Please reset your password', self.email.subject)

    def test_email_to(self):
        """Check the email recipient"""
        self.assertEqual(['john@doe.com'], self.email.to)

    def test_email_body(self):
        """Check the email body for correct content and password reset link"""
        email_body = self.email.body

        # Extract uid and token from email body using regex
        match = re.search(r'/reset/(?P<uidb64>[-\w]+)/(?P<token>[-\w]+)/', email_body)
        self.assertIsNotNone(match, "Password reset link not found in email body")
        uid = match.group('uidb64')
        token = match.group('token')

        # Build expected password reset URL
        password_reset_token_url = reverse('password_reset_confirm', kwargs={
            'uidb64': uid,
            'token': token
        })

        # Assertions
        self.assertIn(password_reset_token_url, email_body)
        self.assertIn('john', email_body)
        self.assertIn('john@doe.com', email_body)
