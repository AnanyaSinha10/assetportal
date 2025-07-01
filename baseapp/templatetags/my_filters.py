from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Custom template filter to allow accessing dictionary items by a variable key.
    Usage: {{ dictionary|get_item:key_variable }}
    """
    return dictionary.get(key)
