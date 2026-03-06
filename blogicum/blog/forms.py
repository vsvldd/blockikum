"""Формы приложения blog."""
from django import forms

from .models import Comment, Post, User


class PostForm(forms.ModelForm):
    """Форма для создания и редактирования публикации."""

    class Meta:
        model = Post
        exclude = ('author',)


class CommentForm(forms.ModelForm):
    """Форма для добавления комментария."""

    class Meta:
        model = Comment
        fields = ('text',)


class UserForm(forms.ModelForm):
    """Форма редактирования профиля пользователя."""

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')
