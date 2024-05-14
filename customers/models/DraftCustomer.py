"""
Model for qcs request
"""
import uuid

from django.core.validators import RegexValidator
from django.db import models
from reversion import revisions as reversion

from Masters.models.CountryCode import CountryCode
from commons.models import BaseModel



class DraftCustomer(BaseModel):
    # f_name = models.CharField(max_length=100, db_column='F_NAME')
    # l_name = models.CharField(max_length=100, db_column="L_NAME")
    # primary_mail = models.EmailField(db_column='EMAIL', max_length=100)
    # password = models.CharField(db_column="PASSWORD", max_length=1000, editable=False)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,13}$',
                                 message="Phone number must be entered in the format: '+999999999'. Up to 13 digits allowed.")
    phone_number = models.CharField(unique=True, validators=[phone_regex], max_length=17, db_column='PHONE_NUMBER')
    country_code = models.ForeignKey(CountryCode, on_delete=models.DO_NOTHING, db_column='COUNTRY_CODE',
                                     related_name='DRAFT_CUSTOMERS')
    otp_generated = models.CharField(max_length=20, blank=True, null=True)
    is_otp_triggered = models.BooleanField(default=False, db_column='IS_OTP_TRIGGERED')


    class Meta:
        """
        class meta
        """
        db_table = 'TRANS_CUSTOMERS_DRAFT_CUSTOMERS'
        app_label = 'customers'
        # TODO add unique togetehr for country code and phone when multiple countrys allowed
        # unique_together = [('proposal_id', 'rfq_no')]


# reversion.register(Sellers)
