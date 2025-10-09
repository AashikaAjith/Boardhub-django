# Create your views here.
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from .models import Board, Topic, Post
from django.db.models import Count
from .forms import NewTopicForm, PostForm
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator

class BoardlistView(ListView): #home page
    model=Board
    context_object_name='boards'
    template_name='home.html'

class TopicListView(ListView):
    model = Topic
    context_object_name = 'topics'
    template_name = 'topics.html'
    paginate_by = 8

    def get_context_data(self, **kwargs):
        kwargs['board'] = self.board 
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        self.board = get_object_or_404(Board, pk=self.kwargs.get('pk'))
        queryset = self.board.topics.order_by('-last_update').annotate(replies=Count('posts') - 1)
        return queryset

class PostListView(ListView):
    model = Post
    context_object_name = 'posts'
    template_name = 'topic_post.html'
    paginate_by = 2  # pagination still works

    def get_queryset(self):
        # Get the topic
        self.topic = get_object_or_404(
            Topic, 
            board__pk=self.kwargs.get('pk'), 
            pk=self.kwargs.get('topic_pk')
        )

        # Separate the first post (main topic post) from replies
        self.main_post = self.topic.posts.first()
        replies = self.topic.posts.exclude(id=self.main_post.id).order_by('-updated_at', '-created_at')
        # updated_at descending, then created_at descending if updated_at is null

        return replies

    def get_context_data(self, **kwargs):
        # Add topic, main post, and mark views
        context = super().get_context_data(**kwargs)
        context['topic'] = self.topic
        context['main_post'] = self.main_post

        if self.request.user.is_authenticated:
            if not self.topic.views.filter(id=self.request.user.id).exists():
                self.topic.views.add(self.request.user)

        return context



@login_required
def new_topic(request, pk):
    board = get_object_or_404(Board, pk=pk)
    

    if request.method == 'POST':
        form = NewTopicForm(request.POST)
        if form.is_valid():
            topic = form.save(commit=False)  # create Topic instance but don't save yet
            topic.board = board
            topic.starter = request.user #actual logged in user
            topic.save()  # save Topic

            Post.objects.create(
                message=form.cleaned_data.get('message'),  # get Post message
                topic=topic,
                created_by=request.user
            )
            return redirect('topic_posts', pk=pk, topic_pk=topic.pk) # redirect to the created topic page
    else:
        form = NewTopicForm()

    return render(request, 'new_topic.html', {'board': board, 'form': form})

@login_required
def reply_topic(request, pk, topic_pk):
    topic = get_object_or_404(Topic, board__pk=pk, pk=topic_pk)
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.topic = topic
            post.created_by = request.user
            post.save()
            return redirect('topic_posts', pk=pk, topic_pk=topic_pk)
    else:
        form = PostForm()
    return render(request, 'reply_topic.html', {'topic': topic, 'form': form})

@method_decorator(login_required, name='dispatch')
class PostUpdateView(UpdateView):
    model=Post
    fields=('message',)
    template_name='edit_post.html'
    pk_url_kwarg='post_pk'
    context_object_name='post'


    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(created_by=self.request.user)
    
    def form_valid(self,form):
        post=form.save(commit=False)
        post.updated_by=self.request.user
        post.updated_at=timezone.now()
        post.save()
        return redirect("topic_posts",pk=post.topic.board.pk,topic_pk=post.topic.pk)