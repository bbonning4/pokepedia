from django import template

register = template.Library()

@register.filter
def starts_with_http(value):
    return value.startswith('http')