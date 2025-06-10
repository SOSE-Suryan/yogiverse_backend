
from django.dispatch import receiver
from django.db.backends.signals import connection_created
from django.db.models.signals import pre_save
from django.utils import timezone
from .models import PasswordResetLinkModel
from datetime import timedelta



RESET_LINK_EXPIRY_MINUTES = 5

@receiver(pre_save, sender=PasswordResetLinkModel)
def at_beginning_save(sender, instance, **kwargs):
    check_if_link_exist = PasswordResetLinkModel.objects.filter(user__email=instance.user.email)
    check_if_link_exist.delete()
    instance.url_link = f"http://yogiverse.in/reset-password/{instance.reset_uuid}/"
    
@receiver(connection_created)
def conn_db(sender, connection, **kwargs):
    expiry_time = timezone.now() - timedelta(minutes=RESET_LINK_EXPIRY_MINUTES)
    PasswordResetLinkModel.objects.filter(created_at__lte=expiry_time).delete()