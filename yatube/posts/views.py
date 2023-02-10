from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post
from .utils import paginate_posts


@cache_page(20)
def index(request):
    posts = Post.objects.select_related('group', 'author').all()
    page_obj = paginate_posts(request, posts, settings.POSTS_PER_PAGE)
    context = {
        "page_obj": page_obj,
    }
    return render(request, "posts/index.html", context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author').all()
    page_obj = paginate_posts(request, posts, settings.POSTS_PER_PAGE)
    context = {
        "group": group,
        "page_obj": page_obj,
    }
    return render(request, "posts/group_list.html", context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author__username=username)
    total_posts = posts.count()
    page_obj = paginate_posts(request, posts, settings.POSTS_PER_PAGE)
    following = request.user.is_authenticated and author.following.filter(
        user=request.user).exists()
    context = {
        "total_posts": total_posts,
        "author": author,
        "page_obj": page_obj,
        "following": following,
    }
    return render(request, "posts/profile.html", context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    author = post.author
    form = CommentForm()
    comments = post.comments.select_related('author').all()
    total_posts = Post.objects.filter(author=post.author).count()
    following = request.user.is_authenticated and author.following.filter(
        user=request.user
    ).exists()
    context = {
        "author": post.author,
        "post": post,
        "total_posts": total_posts,
        "comments": comments,
        "form": form,
        "following": following,
    }
    return render(request, "posts/post_detail.html", context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        form.instance.author = request.user
        form.save()
        return redirect("posts:profile", username=request.user.username)
    context = {"form": form, "groups": Group.objects.all()}
    return render(request, "posts/create_post.html", context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return HttpResponseForbidden()
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect("posts:post_detail", post_id=post_id)

    context = {
        "post_id": post.id,
        "is_edit": True,
        "form": form,
    }
    return render(request, "posts/create_post.html", context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = paginate_posts(request, posts, settings.POSTS_PER_PAGE)
    context = {"page_obj": page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    following = Follow.objects.filter(
        author=author,
        user=request.user
    ).exists()
    if request.user != author and not following:
        follow = Follow.objects.create(
            user=request.user,
            author=author
        )
        follow.save()
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    Follow.objects.filter(
        user=request.user, author__username=username).delete()
    return redirect("posts:profile", username)
