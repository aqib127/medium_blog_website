from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Article

@receiver(pre_save, sender=Article)
def calculate_read_mins(sender, instance, **kwargs):
    word_count = len(instance.body.split())
    instance.read_mins = max(1, round(word_count / 200))
