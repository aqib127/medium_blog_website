import re
from django.core.exceptions import ValidationError
from django.utils.text import slugify

HEX_COLOR_RE = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'


def generate_unique_slug(model, field, value):
    # allow_unicode=True so non-Latin names (Arabic, Chinese, Cyrillic, ...)
    # produce meaningful handles instead of collapsing to 'untitled'.
    slug = slugify(value, allow_unicode=True) or 'untitled'
    if not model.objects.filter(**{field: slug}).exists():
        return slug
    base = slug
    count = 1
    while True:
        new_slug = f"{base}-{count}"
        if not model.objects.filter(**{field: new_slug}).exists():
            return new_slug
        count += 1


def validate_hex_color(color):
    if not re.match(HEX_COLOR_RE, color):
        raise ValidationError('Enter a valid hex color (e.g. "#1F4E4A").')
