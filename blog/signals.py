from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile
from .tasks import send_async_mail


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance, role=0,
                               name=instance.first_name+' '+instance.last_name)
        send_async_mail.apply_async(
            args=[
                'Useful Python',
                'Welcome to Useful Python! Learn about useful Python libraries and techniques to make your tasks more efficient and automated. You can also find many ready-to-use tools to make use of right away! You can contact us anytime through this email address.',
                'usefulpython.in@gmail.com',
                [instance.email]
            ]
        )