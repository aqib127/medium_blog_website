import re
from django.utils.text import slugify

def generate_unique_slug(model, field, value):
    slug = slugify(value) or 'untitled'
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
    return bool(re.match(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', color))
