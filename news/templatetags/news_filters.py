from django import template

from ..models import Post

register = template.Library()


@register.simple_tag
def get_posts(max_posts):
    """
    Returns all Posts
    """
    posts = Post.objects.filter(is_published=True)

    if max_posts and len(posts) > max_posts:
        posts = posts[:max_posts]

    return posts
