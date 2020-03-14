from django.shortcuts import get_object_or_404
from .models import User
from django.db.models import Count

def get_profile(username):
    """Return User object with counts of all related models"""
    return get_object_or_404(User.objects.annotate(
        post_count=Count('post_author', distinct=True),
        followers_count=Count('following', distinct=True),
        following_count=Count('follower', distinct=True)),
        username=username)