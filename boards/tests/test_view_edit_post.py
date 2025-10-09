from django.forms import ModelForm
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve, reverse

from ..models import Board, Post, Topic
from ..views import PostUpdateView


class PostUpdateViewTestCase(TestCase):
    """
    Base test case to set up common objects for all PostUpdateView tests:
    - Board
    - User
    - Topic
    - Post
    - URL for editing the post
    """
    def setUp(self):
        self.board = Board.objects.create(name='Django', description='Django board.')
        self.username = 'john'
        self.password = '123'
        self.user = User.objects.create_user(
            username=self.username, email='john@doe.com', password=self.password
        )
        self.topic = Topic.objects.create(subject='Hello, world', board=self.board, starter=self.user)
        self.post = Post.objects.create(message='Lorem ipsum dolor sit amet', topic=self.topic, created_by=self.user)
        self.url = reverse('edit_post', kwargs={
            'pk': self.board.pk,
            'topic_pk': self.topic.pk,
            'post_pk': self.post.pk
        })


class LoginRequiredPostUpdateViewTests(PostUpdateViewTestCase):
    """Test that login is required to edit a post"""
    def test_redirection_for_anonymous_user(self):
        login_url = reverse('login')
        response = self.client.get(self.url)
        self.assertRedirects(response, f'{login_url}?next={self.url}')


class UnauthorizedPostUpdateViewTests(PostUpdateViewTestCase):
    """Test that a user who did not create the post cannot edit it"""
    def setUp(self):
        super().setUp()
        # Create a different user and login
        self.other_user = User.objects.create_user(username='jane', email='jane@doe.com', password='321')
        self.client.login(username='jane', password='321')
        self.response = self.client.get(self.url)

    def test_status_code_returns_404(self):
        """Unauthorized users should get a 404 page not found"""
        self.assertEqual(self.response.status_code, 404)


class PostUpdateViewTests(PostUpdateViewTestCase):
    """Test the post update view for the post owner"""
    def setUp(self):
        super().setUp()
        self.client.login(username=self.username, password=self.password)
        self.response = self.client.get(self.url)

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_view_class(self):
        """Ensure the view resolves to PostUpdateView"""
        view = resolve(self.url)
        self.assertEqual(view.func.view_class, PostUpdateView)

    def test_csrf_token_present(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    def test_contains_form_instance(self):
        form = self.response.context.get('form')
        self.assertIsInstance(form, ModelForm)

    def test_form_inputs(self):
        """
        The form should contain:
        - One textarea for message
        """
        self.assertContains(self.response, '<textarea', 1)

    def test_csrf_present(self):
        """The page must have a CSRF token in the HTML"""
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    

class SuccessfulPostUpdateViewTests(PostUpdateViewTestCase):
    """Test submitting valid data updates the post"""
    def setUp(self):
        super().setUp()
        self.client.login(username=self.username, password=self.password)
        self.response = self.client.post(self.url, {'message': 'edited message'})

    def test_redirection_after_success(self):
        """After a successful edit, user is redirected to topic posts page"""
        topic_posts_url = reverse('topic_posts', kwargs={'pk': self.board.pk, 'topic_pk': self.topic.pk})
        self.assertRedirects(self.response, topic_posts_url)

    def test_post_is_updated(self):
        """The post message should be updated in the database"""
        self.post.refresh_from_db()
        self.assertEqual(self.post.message, 'edited message')


class InvalidPostUpdateViewTests(PostUpdateViewTestCase):
    """Test submitting invalid data (empty form)"""
    def setUp(self):
        super().setUp()
        self.client.login(username=self.username, password=self.password)
        self.response = self.client.post(self.url, {})

    def test_status_code_returns_200(self):
        """Invalid submission should re-render the page"""
        self.assertEqual(self.response.status_code, 200)

    def test_form_errors_present(self):
        form = self.response.context.get('form')
        self.assertTrue(form.errors)
