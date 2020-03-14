from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.views.decorators.cache import cache_page
from .utils import get_profile
from .forms import PostForm, CommentForm
from .models import *


def index(request):
    """Display latest posts."""
    post_list = Post.objects.order_by("-pub_date").annotate(comment_count=Count('comment_post')).prefetch_related(
        'author', 'group').all()
    paginator = Paginator(post_list, 10)

    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html', {'page': page, 'paginator': paginator})


def group_posts(request, slug):
    """Display latest posts in the group."""

    group = get_object_or_404(Group, slug=slug)

    post_list = Post.objects.filter(group=group).annotate(comment_count=Count('comment_post')).order_by(
        "-pub_date").prefetch_related('author', 'group').all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    return render(request, 'group.html', {'group': group, 'page': page, 'paginator': paginator})


@login_required
def new_post(request):
    """Display a form for adding a new post to authenticated users."""
    if request.method == 'POST':
        form = PostForm(request.POST, files=request.FILES or None)
        if form.is_valid():
            # if form is valid, populate missing data and save a post
            # all validation is done at the model level
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('index')
        return render(request, 'new_post.html', {'form': form})
    form = PostForm()
    return render(request, 'new_post.html', {'form': form})


def profile(request, username):
    """Display profile information and user's latest posts."""
    profile = get_profile(username)

    post_list = Post.objects.filter(author=profile).annotate(
        comment_count=Count('comment_post', distinct=True)).order_by("-pub_date").select_related(
            'author').prefetch_related('group').all()

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    following = request.user.is_authenticated and Follow.objects.filter(user=request.user, author = profile).exists()

    context = {
        'profile': profile,
        'following': following,
        'page': page,
        'paginator': paginator
    }
    return render(request, 'profile.html', context)


def post_view(request, username, post_id):
    """View a post."""
    # if post or author not found, or author's username is wrong, return 404.
    profile = get_profile(username)
    post_object = get_object_or_404(
        Post.objects.select_related('author').annotate(
            comment_count=Count('comment_post', distinct=True)),
            id=post_id,
            author=profile)

    comments = Comment.objects.filter(post=post_object).order_by("-created").select_related('post').prefetch_related(
        'author').all()

    following = request.user.is_authenticated and Follow.objects.filter(user=request.user, author=profile).exists()
    form = CommentForm()
    context = {
        'profile': profile,
        'post': post_object,
        'following': following,
        'form': form,
        'comments': comments
    }
    return render(request, "post.html", context)


def post_edit(request, username, post_id):
    """Display a form for editing a post."""
    # only post author can edit post
    if request.user.username != username:
        return redirect('post', username=username, post_id=post_id)

    # get post to be edited
    # return 404 if User with username does not exist, if Post with
    # post_id does not exist or if username is not the author of the Post.
    post_object = get_object_or_404(Post, id=post_id, author__username=username)

    if request.method == 'POST':
        form = PostForm(request.POST, files=request.FILES or None, instance=post_object)
        if form.is_valid():
            form.save()
            return redirect('post', username=username, post_id=post_id)
        return render(request, 'edit_post.html', {'form': form})

    form = PostForm(instance=post_object)
    # post is absolutely not required here, but without it code fails one test
    return render(request, 'edit_post.html', {'form': form, 'post': post_object})


@login_required
def add_comment(request, username, post_id):
    """Display a form for adding a comment."""
    # get post to which comment is to be added
    # return 404 if User with username does not exist, if Post with
    # post_id does not exist or if username is not the author of the Post.
    post_object = get_object_or_404(Post, id=post_id, author__username=username)

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            # if form is valid, populate missing data and save a post
            # all validation is done at the model level
            comment = form.save(commit=False)
            comment.post = post_object
            comment.author = request.user
            comment.save()
            return redirect('post', username=username, post_id=post_id)
        return render(request, 'comments.html', {'form': form, 'post': post_object})
    form = CommentForm()
    return render(request, 'comments.html', {'form': form, 'post': post_object})


@login_required
def follow_index(request):
    """Display all posts from authors whom active user follows."""
    post_list = Post.objects.order_by("-pub_date").annotate(
        comment_count=Count('comment_post', distinct=True)).prefetch_related(
        'author', 'group', 'author__following').filter(author__following__user=request.user).all()
    paginator = Paginator(post_list, 10)

    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'follow.html', {'page': page, 'paginator': paginator})


@login_required
def profile_follow(request, username):
    """Create a new Follow object where active user follows username's profile."""
    if request.user.username != username:
        # can't follow yourself
        if not Follow.objects.filter(author__username=username, user= request.user).exists():
            # prevent duplicate followings
            author = get_object_or_404(User, username=username)
            follow = Follow.objects.create(user=request.user, author=author)
            follow.save()
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    """Delete a Follow object where active user follows username's profile."""
    follow = get_object_or_404(Follow, author__username=username, user=request.user)
    follow.delete()
    return redirect('profile', username=username)


def page_not_found(request, exception):
    """Display error 4040 page."""
    return render(request, "misc/404.html", {"path": request.path}, status=404)


def server_error(request):
    """Display error 500 page."""
    return render(request, "misc/500.html", status=500)
