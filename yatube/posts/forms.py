from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["text", "group", "image"]
        widgets = {
            "text": forms.Textarea(attrs={"required": True}),
            "group": forms.Select(attrs={"required": False}),
        }
        labels = {
            "text": "Текст сообщения",
            "group": "Группа",
        }
        help_texts = {
            "text": "Введите текст сообщения",
            "group": "Выберите группу, "
            "в которую хотите опубликовать сообщение",
        }


class CommentForm(forms.ModelForm):
    class Meta():
        model = Comment
        fields = ['text', ]
        labels = {
            'text': 'Текст комментария',
        }
        help_texts = {
            'text': 'Ваш комментарий',
        }
