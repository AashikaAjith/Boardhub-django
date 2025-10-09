# boards/tests/test_view_reply_topic.py
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve, reverse

from ..forms import PostForm
from ..models import Board, Post, Topic
from ..views import reply_topic


class ReplyTopicTestCase(TestCase):
    """Base test case for reply_topic view tests"""
    def setUp(self):
        self.board = Board.objects.create(name='Django', description='Django board.')
        self.username = 'john'
        self.password = '123'
        self.user = User.objects.create_user(
            username=self.username,
            email='john@doe.com',
            password=self.password
        )
        self.topic = Topic.objects.create(
            subject='Hello, world',
            board=self.board,
            starter=self.user
        )
        # First post in the topic
        Post.objects.create(
            message='Lorem ipsum dolor sit amet',
            topic=self.topic,
            created_by=self.user
        )
        self.url = reverse('reply_topic', kwargs={'pk': self.board.pk, 'topic_pk': self.topic.pk})


class LoginRequiredReplyTopicTests(ReplyTopicTestCase):
    """Ensure login required for replying"""
    def test_redirection(self):
        login_url = reverse('login')
        response = self.client.get(self.url)
        self.assertRedirects(response, f'{login_url}?next={self.url}')


class ReplyTopicTests(ReplyTopicTestCase):
    """Tests for GET request to reply_topic"""
    def setUp(self):
        super().setUp()
        self.client.login(username=self.username, password=self.password)
        self.response = self.client.get(self.url)

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_view_function(self):
        view = resolve(self.url)
        self.assertEqual(view.func, reply_topic)

    def test_csrf(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    def test_contains_form(self):
        form = self.response.context.get('form')
        self.assertIsInstance(form, PostForm)

    def test_form_inputs(self):
        """The view must contain one textarea and csrf token in the response"""
        # Check textarea in form
        form = self.response.context.get('form')
        self.assertIsNotNone(form)
        self.assertContains(self.response, '<textarea', 1)

        # Check CSRF token in response HTML
        self.assertContains(self.response, 'csrfmiddlewaretoken')

class SuccessfulReplyTopicTests(ReplyTopicTestCase):
    """POST valid reply"""
    def setUp(self):
        super().setUp()
        self.client.login(username=self.username, password=self.password)
        self.response = self.client.post(self.url, {'message': 'Hello, world!'})

    def test_redirection(self):
        topic_posts_url = reverse(
            'topic_posts',
            kwargs={'pk': self.board.pk, 'topic_pk': self.topic.pk}
        )
        self.assertRedirects(self.response, topic_posts_url)

    def test_reply_created(self):
        self.assertEqual(Post.objects.count(), 2)

    def test_reply_user(self):
        """Check that the new post belongs to the correct user"""
        new_post = Post.objects.last()
        self.assertEqual(new_post.created_by, self.user)

    def test_topic_views_not_affected(self):
        """Views count should remain same after posting reply"""
        self.assertEqual(self.topic.views.count(), 0)


class InvalidReplyTopicTests(ReplyTopicTestCase):
    """POST invalid reply (empty message)"""
    def setUp(self):
        super().setUp()
        self.client.login(username=self.username, password=self.password)
        self.response = self.client.post(self.url, {})

    def test_status_code(self):
        """Should return the same page with errors"""
        self.assertEqual(self.response.status_code, 200)

    def test_form_errors(self):
        form = self.response.context.get('form')
        self.assertTrue(form.errors)


class TopicViewsTests(ReplyTopicTestCase):
    """Test topic views counter (ManyToManyField)"""
    def setUp(self):
        super().setUp()
        self.client.login(username=self.username, password=self.password)
        self.topic_posts_url = reverse('topic_posts', kwargs={'pk': self.board.pk, 'topic_pk': self.topic.pk})

    def test_view_increment_once_per_user(self):
        self.client.get(self.topic_posts_url)
        self.topic.refresh_from_db()
        self.assertEqual(self.topic.views.count(), 1)

        # Second GET should not increment
        self.client.get(self.topic_posts_url)
        self.topic.refresh_from_db()
        self.assertEqual(self.topic.views.count(), 1)

    def test_another_user_view(self):
        other_user = User.objects.create_user(username='jane', password='123')
        self.client.login(username='jane', password='123')
        self.client.get(self.topic_posts_url)
        self.topic.refresh_from_db()
        self.assertEqual(self.topic.views.count(), 1)

        # Original user views again
        self.client.login(username=self.username, password=self.password)
        self.client.get(self.topic_posts_url)
        self.topic.refresh_from_db()
        self.assertEqual(self.topic.views.count(), 2)
