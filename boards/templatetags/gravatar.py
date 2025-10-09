import hashlib
from urllib.parse import urlencode

from django import template

register = template.Library()

@register.filter
def gravatar(user, size=256):
    """
    Returns the Gravatar URL for a user object.
    Usage in template: {{ user|gravatar:100 }}
    """
    if not user.email:
        return ''  # No email, return empty string

    email = user.email.strip().lower().encode('utf-8')
    default = 'mm'  # default mystery man
    params = urlencode({'d': default, 's': str(size)})
    url = f'https://www.gravatar.com/avatar/{hashlib.md5(email).hexdigest()}?{params}'
    return url
