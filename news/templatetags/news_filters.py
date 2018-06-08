from django import template

from ..models import Post

register = template.Library()


@register.assignment_tag
def get_posts():
    """
    Returns all Posts
    """
    return Post.objects.filter(is_published=True)
