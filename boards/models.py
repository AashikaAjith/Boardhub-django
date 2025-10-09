# Create your models here.


from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from markdown import markdown
from django.utils.html import mark_safe


class Board(models.Model):
    name=models.CharField(max_length=30,unique=True)
    description=models.CharField(max_length=100)
    def __str__(self):
        return self.name

    def get_posts_count(self):
        return Post.objects.filter(topic__board=self).count()

    def get_last_post(self):
        return Post.objects.filter(topic__board=self).order_by('-created_at').first()


class Topic(models.Model):
    subject=models.CharField(max_length=500)
    last_update=models.DateTimeField(auto_now=True)
    board=models.ForeignKey(Board,related_name='topics',on_delete=models.CASCADE)
    starter=models.ForeignKey(User,related_name='started_topics',on_delete=models.CASCADE)
    views = models.ManyToManyField(User, related_name='viewed_topics', blank=True)

    def __str__(self):
        return self.subject

    def get_replies_count(self):
        """Number of replies (excluding the first post)"""
        return max(self.posts.count() - 1, 0)

    def get_last_post(self):
        """Return the latest post in this topic"""
        return self.posts.order_by('-created_at').first()

    def get_last_post_url(self):
        """URL to view the last post"""
        last_post = self.get_last_post()
        if last_post:
            return reverse('topic_posts', kwargs={'pk': self.board.pk, 'topic_pk': self.pk}) + f"#post-{last_post.pk}"
        return '#'




class Post(models.Model):
    message=models.TextField(max_length=5000)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(null=True)
    topic=models.ForeignKey(Topic,related_name="posts",on_delete=models.CASCADE)
    created_by=models.ForeignKey(User,related_name="created_posts",on_delete=models.CASCADE)
    updated_by=models.ForeignKey(User,related_name="+",null=True,on_delete=models.CASCADE)

    def __str__(self):
        return self.message[:30]

    def get_absolute_url(self):
        """Anchor link for this post, useful for 'last post' links"""
        return reverse('topic_posts', kwargs={'pk': self.topic.board.pk, 'topic_pk': self.topic.pk}) + f"#post-{self.pk}"


    def get_message_as_markdown(self):
        return mark_safe(markdown(self.message,safe_mode='escape'))
    
