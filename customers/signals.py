import base64

import pyotp
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from customers.logger import draft_customer_signal_log, customer_signal_log
from customers.models.Customers import Customers
from customers.models.DraftCustomer import DraftCustomer


@receiver(post_save, sender=DraftCustomer)
def DraftCustomer_postsave(sender, instance, **kwargs):
    """
    Turn clarification_requested true for QCS request when clarification requested
    :param sender: ClarificationRequest
    :param instance: clarification request instance
    :param kwargs:
    :return:
    """
    draft_customer_signal_log.info(f'In DraftCustomer_postsave instance -- {instance}')

    print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%", instance, kwargs)
    totp = pyotp.TOTP(base64.b32encode(instance.phone_number.encode()))
    otp = totp.now()
    # TODO send mail and generate OTP here
    # instance.otp_generated = otp
    # instance.is_otp_triggered = True
    # instance.save()
    DraftCustomer.objects.filter(pk=instance.pk).update(is_otp_triggered=True, otp_generated=otp)
    draft_customer_signal_log.info("Successfully executed DraftCustomer_postsave")


@receiver(post_save, sender=Customers)
def Customer_postsave(sender, instance, **kwargs):
    """
    Turn clarification_requested true for QCS request when clarification requested
    :param sender: ClarificationRequest
    :param instance: clarification request instance
    :param kwargs:
    :return:
    """
    draft_customer_signal_log.info(f'In DraftCustomer_postsave instance -- {instance}')

    print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%", instance, kwargs)
    totp = pyotp.TOTP(base64.b32encode(instance.phone_number.encode()))
    otp = totp.now()
    # TODO send mail and generate OTP here
    # instance.otp_generated = otp
    # instance.is_otp_triggered = True
    # instance.save()
    Customers.objects.filter(pk=instance.pk).update(is_otp_triggered=True, otp_generated=otp)
    customer_signal_log.info("Successfully executed Customer_postsave")






