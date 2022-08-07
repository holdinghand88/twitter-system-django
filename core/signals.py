from django.db.models.signals import post_save
from django.dispatch import receiver
from .tasks import test
from .models import AutoLikeSetting

@receiver(post_save, sender=AutoLikeSetting)
def autolike_job(sender, instance, created, **kwargs):
    print(instance.id)
    test.apply_async(args=[instance.id,], serializer="json")