"""Вью-функции приложения blog."""
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm, UserForm
from .models import Category, Comment, Post, User


# Настройка пагинации
ITEMS_ON_PAGE = 10


def filter_posts(**filters):
    """Возвращает отфильтрованный QuerySet публикаций."""
    return Post.objects.select_related(
        'author',
        'category',
        'location',
    ).annotate(
        comment_count=Count('comments')
    ).filter(**filters).order_by('-pub_date')


def paginate_queryset(request, queryset, per_page=ITEMS_ON_PAGE):
    """Создаёт объект пагинации для переданного QuerySet."""
    paginator = Paginator(queryset, per_page)
    page_num = request.GET.get('page')
    return paginator.get_page(page_num)


def index(request):
    """Главная страница блога."""
    post_list = filter_posts(
        is_published=True,
        category__is_published=True,
        pub_date__lte=datetime.now()
    )
    page_obj = paginate_queryset(request, post_list)
    return render(request, 'blog/index.html', {'page_obj': page_obj})


def category_posts(request, category_slug):
    """Страница категории с публикациями."""
    category_obj = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )
    post_list = filter_posts(
        is_published=True,
        category__is_published=True,
        pub_date__lte=datetime.now(),
        category=category_obj
    )
    page_obj = paginate_queryset(request, post_list)
    return render(
        request,
        'blog/post_list.html',
        {'category': category_obj, 'page_obj': page_obj}
    )


def post_detail(request, post_id):
    """Детальная страница публикации."""
    post_obj = get_object_or_404(Post, id=post_id)
    if request.user != post_obj.author:
        post_obj = get_object_or_404(
            Post,
            id=post_id,
            is_published=True,
            category__is_published=True,
            pub_date__lte=datetime.now()
        )
    comment_form = CommentForm(request.POST or None)
    comment_list = Comment.objects.select_related('author').filter(post=post_obj)
    return render(
        request,
        'blog/post_detail.html',
        {'post': post_obj, 'form': comment_form, 'comments': comment_list}
    )


@login_required
def create_post(request):
    """Создание новой публикации."""
    post_form = PostForm(request.POST or None, files=request.FILES or None)
    if post_form.is_valid():
        new_post = post_form.save(commit=False)
        new_post.author = request.user
        new_post.save()
        return redirect('blog:profile', request.user)
    return render(request, 'blog/create.html', {'form': post_form})


@login_required
def edit_post(request, post_id):
    """Редактирование существующей публикации."""
    post_obj = get_object_or_404(Post, id=post_id)
    if request.user != post_obj.author:
        return redirect('blog:post_detail', post_id)
    post_form = PostForm(request.POST or None, instance=post_obj)
    if post_form.is_valid():
        post_form.save()
        return redirect('blog:post_detail', post_id)
    return render(request, 'blog/create.html', {'form': post_form})


@login_required
def delete_post(request, post_id):
    """Удаление публикации автором."""
    post_obj = get_object_or_404(Post, id=post_id)
    if request.user != post_obj.author:
        return redirect('blog:post_detail', post_id)
    post_form = PostForm(request.POST or None, instance=post_obj)
    if request.method == 'POST':
        post_obj.delete()
        return redirect('blog:index')
    return render(request, 'blog/create.html', {'form': post_form})


@login_required
def add_comment(request, post_id):
    """Добавление нового комментария."""
    post_obj = get_object_or_404(Post, id=post_id)
    comment_form = CommentForm(request.POST or None)
    if comment_form.is_valid():
        new_comment = comment_form.save(commit=False)
        new_comment.author = request.user
        new_comment.post = post_obj
        new_comment.save()
    return redirect('blog:post_detail', post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    """Редактирование комментария автором."""
    comment_obj = get_object_or_404(Comment, id=comment_id)
    if request.user != comment_obj.author:
        return redirect('blog:post_detail', post_id)
    comment_form = CommentForm(request.POST or None, instance=comment_obj)
    if comment_form.is_valid():
        comment_form.save()
        return redirect('blog:post_detail', post_id)
    return render(
        request,
        'blog/comment.html',
        {'comment': comment_obj, 'form': comment_form}
    )


@login_required
def delete_comment(request, post_id, comment_id):
    """Удаление комментария автором."""
    comment_obj = get_object_or_404(Comment, id=comment_id)
    if request.user != comment_obj.author:
        return redirect('blog:post_detail', post_id)
    if request.method == 'POST':
        comment_obj.delete()
        return redirect('blog:post_detail', post_id)
    return render(request, 'blog/comment.html', {'comment': comment_obj})


def profile(request, username):
    """Страница профиля пользователя."""
    user_profile = get_object_or_404(User, username=username)
    post_list = filter_posts(author=user_profile)
    if request.user != user_profile:
        post_list = filter_posts(
            is_published=True,
            category__is_published=True,
            pub_date__lte=datetime.now(),
            author=user_profile
        )
    page_obj = paginate_queryset(request, post_list)
    return render(
        request,
        'blog/profile.html',
        {'profile': user_profile, 'page_obj': page_obj}
    )


@login_required
def edit_profile(request):
    """Редактирование профиля пользователя."""
    user_profile = get_object_or_404(User, username=request.user)
    profile_form = UserForm(request.POST or None, instance=user_profile)
    if profile_form.is_valid():
        profile_form.save()
        return redirect('blog:profile', request.user)
    return render(request, 'blog/user.html', {'form': profile_form})
