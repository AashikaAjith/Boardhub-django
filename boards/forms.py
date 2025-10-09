# boards/forms.py
from django import forms
from .models import Topic,Post

class NewTopicForm(forms.ModelForm):
    # This field is not part of Topic, it's for Post
    message = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5, 'placeholder': 'What is on your mind?'}),
        max_length=4000,
        help_text='The max length of the text is 4000.'
    )

    class Meta:
        model = Topic
        fields = ['subject', 'message']  # subject comes from Topic, message from Post

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['message', ]
        widgets = {
            'message': forms.Textarea(attrs={'id': 'id_message'}),
        }