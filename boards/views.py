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

#logging system
import logging

logger = logging.getLogger(__name__)
'''
def test_log(request):
    logger.debug("This is a DEBUG message — for developers.")
    logger.info("This is an INFO message — normal app info.")
    logger.warning("This is a WARNING message — something might be wrong.")
    logger.error("This is an ERROR message — something went wrong.")
    logger.critical("This is a CRITICAL message — very serious issue.")
    return HttpResponse("Logging test done! Check your terminal.")

'''
class BoardlistView(ListView): #home page
    model=Board
    context_object_name='boards'
    template_name='home.html'

    def get(self,request,*args,**kwargs):
        logger.info("home page is viewd by user:%s",request.user)
        return super().get(request,*args, **kwargs)

class TopicListView(ListView):#within each board , what are the topics listed

    model = Topic
    context_object_name = 'topics'
    template_name = 'topics.html'
    paginate_by = 8

    def get_context_data(self, **kwargs):
        kwargs['board'] = self.board 
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        board_id=self.kwargs.get("pk")
        try:
            self.board = get_object_or_404(Board, pk=board_id)
            logger.info("user %s viewing topics of board id %s",self.request.user,board_id)
            queryset = self.board.topics.order_by('-last_update').annotate(replies=Count('posts') - 1)
            return queryset
        except Exception as e:
            logger.error("error in fetching topisc for the board %s:%s",board_id,e)
            raise

class PostListView(ListView): #innside the topic what are post avail

    model = Post
    context_object_name = 'posts'
    template_name = 'topic_post.html'
    paginate_by = 2  # pagination still works

    def get_queryset(self):
        # Get the topic
        board_id=self.kwargs.get('pk')
        topic_id=self.kwargs.get('topic_pk')
     
        try:
            self.topic = get_object_or_404(Topic, board__pk=board_id, pk=topic_id)
            logger.info("User %s viewing topic ID %s on board %s", self.request.user, topic_id, board_id)
            # Separate the first post (main topic post) from replies
            self.main_post = self.topic.posts.first()
            replies = self.topic.posts.exclude(id=self.main_post.id).order_by('-updated_at', '-created_at')
            # updated_at descending, then created_at descending if updated_at is null
            return replies
        
        except Exception as e:
            logger.error("Error fetching posts for topic %s: %s", topic_id, e)
            raise

    def get_context_data(self, **kwargs):
        # Add topic, main post, and mark views
        context = super().get_context_data(**kwargs)
        context['topic'] = self.topic
        context['main_post'] = self.main_post

        if self.request.user.is_authenticated:
            if not self.topic.views.filter(id=self.request.user.id).exists():
                self.topic.views.add(self.request.user)
                logger.debug("User %s marked as viewed for topic %s", self.request.user, self.topic.id)
        return context

@login_required
def new_topic(request, pk): #when the user wants to create a new topic

    board = get_object_or_404(Board, pk=pk)
    logger.info("User %s opened new topic form for board %s", request.user, board)
    

    if request.method == 'POST':
        form = NewTopicForm(request.POST)
        if form.is_valid():
            topic = form.save(commit=False)  # create Topic instance but don't save yet
            topic.board = board
            topic.starter = request.user #actual logged in user
            topic.save()  # save Topic
            logger.info("New topic '%s' created by user %s in board %s", topic.subject, request.user, board)

            Post.objects.create(
                message=form.cleaned_data.get('message'),  # get Post message
                topic=topic,
                created_by=request.user
            )
            return redirect('topic_posts', pk=pk, topic_pk=topic.pk) # redirect to the created topic page
        else:
          logger.warning("Invalid topic form submitted by user %s: %s", request.user, form.errors)  
    else:
        logger.debug("New topic GET request by user %s", request.user)
        form = NewTopicForm()

    return render(request, 'new_topic.html', {'board': board, 'form': form})

@login_required
def reply_topic(request, pk, topic_pk):#with each post reply 

    topic = get_object_or_404(Topic, board__pk=pk, pk=topic_pk)
    logger.info("User %s opened reply form for topic %s", request.user, topic)
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.topic = topic
            post.created_by = request.user
            post.save()
            logger.info("User %s replied to topic %s", request.user, topic)
            return redirect('topic_posts', pk=pk, topic_pk=topic_pk)
        else:
            logger.warning("Invalid reply form by %s: %s", request.user, form.errors)
    else:
        logger.debug("Reply page opened by user %s", request.user)
        form = PostForm()
    return render(request, 'reply_topic.html', {'topic': topic, 'form': form})

@method_decorator(login_required, name='dispatch')
class PostUpdateView(UpdateView): #modifing existing post or reply
    model=Post
    fields=('message',)
    template_name='edit_post.html'
    pk_url_kwarg='post_pk'
    context_object_name='post'


    def get_queryset(self):
        queryset = super().get_queryset()
        logger.debug("Fetching posts editable by user %s", self.request.user)
        return queryset.filter(created_by=self.request.user)
    
    def form_valid(self,form):
        post=form.save(commit=False)
        post.updated_by=self.request.user
        post.updated_at=timezone.now()
        post.save()
        logger.info("User %s updated post %s", self.request.user, post.id)
        return redirect("topic_posts",pk=post.topic.board.pk,topic_pk=post.topic.pk)