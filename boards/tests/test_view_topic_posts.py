from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve, reverse

from ..models import Board, Post, Topic
from ..views import PostListView


class TopicPostsTests(TestCase):
    def setUp(self):
        self.board = Board.objects.create(name='Django', description='Django board.')
        self.user = User.objects.create_user(username='john', email='john@doe.com', password='123')
        self.topic = Topic.objects.create(subject='Hello, world', board=self.board, starter=self.user)
        Post.objects.create(message='Lorem ipsum dolor sit amet', topic=self.topic, created_by=self.user)
        self.url = reverse('topic_posts', kwargs={'pk': self.board.pk, 'topic_pk': self.topic.pk})
        self.response = self.client.get(self.url)

    def test_status_code(self):
        """The topic posts page should return a 200 (OK) response."""
        self.assertEqual(self.response.status_code, 200)

    def test_view_function(self):
        """The URL /boards/1/topics/1/ should be resolved by topic_posts view."""
        view = resolve(f'/boards/{self.board.pk}/topics/{self.topic.pk}/')
        self.assertEqual(view.func.view_class, PostListView)
