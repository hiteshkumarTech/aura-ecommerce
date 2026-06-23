"""Template tag to update query-string params while preserving the rest.

Keeps filters/search intact across pagination links, e.g. ?q=bag&page=2.
"""
from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def query_transform(context, **kwargs):
    query = context["request"].GET.copy()
    for key, value in kwargs.items():
        query[key] = value
    return query.urlencode()
