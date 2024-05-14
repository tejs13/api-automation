"""
Model for qcs request
"""
import uuid

from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db import models
from reversion import revisions as reversion

from Masters.models.CountryCode import CountryCode
from commons.models import BaseModel



class Customers(BaseModel):
    cust_id = models.CharField(max_length=100, db_column="CUST_ID", unique=True, blank=True, null=True)
    cust_uuid = models.UUIDField(default=uuid.uuid4, db_column="CUST_UUID",editable=False, unique=True)
    cust_user_obj = models.OneToOneField(User, on_delete=models.DO_NOTHING, blank=True, null=True,
                                           db_column='CUST_USER_OBJ', related_name='CUSTOMERS')


    f_name = models.CharField(max_length=100, db_column='F_NAME', blank=True, null=True)
    l_name = models.CharField(max_length=100, db_column="L_NAME", blank=True, null=True)
    primary_mail = models.EmailField(db_column='EMAIL', max_length=100, blank=True, null=True)
    # password = models.CharField(db_column="PASSWORD", max_length=1000, editable=False)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,13}$',
                                 message="Phone number must be entered in the format: '+999999999'. Up to 13 digits allowed.")
    phone_number = models.CharField(unique=True, validators=[phone_regex], max_length=17, db_column='PHONE_NUMBER')
    country_code = models.ForeignKey(CountryCode, on_delete=models.DO_NOTHING, db_column='COUNTRY_CODE',
                                     related_name='CUSTOMERS')
    otp_generated = models.CharField(max_length=20, blank=True, null=True)
    is_otp_triggered = models.BooleanField(default=False, db_column='IS_OTP_TRIGGERED')

    def __str__(self):
        return str(self.cust_uuid) + '--' + str(self.f_name)

    class Meta:
        """
        class meta
        """
        db_table = 'TRANS_CUSTOMERS_CUSTOMERS'
        app_label = 'customers'
        # unique_together = [('proposal_id', 'rfq_no')]


reversion.register(Customers)
