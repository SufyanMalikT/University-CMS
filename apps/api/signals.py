from django.db.models.signals import post_save
from django.dispatch import receiver
from ..accounts.models import CustomUser, Student

@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    print("hello")
    if created:
        Student.objects.create(user=instance)