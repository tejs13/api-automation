"""
Model for qcs request
"""

from django.core.validators import FileExtensionValidator
from django.db import models
from reversion import revisions as reversion

from Sellers.constants import ACCEPTED_TYPES
from Sellers.models.SellerProduct import SellerProduct
from Sellers.validators import file_size
from commons.models import BaseModel



class BannerAndProducts(BaseModel):
    banner_img = models.FileField(upload_to="BANNERS/%Y/%m/%d/", db_column="BANNERS",
                                  validators=[FileExtensionValidator(allowed_extensions=ACCEPTED_TYPES), file_size])
    banner_desc = models.TextField(db_column='BANNER_DESC', blank=True, null=True)

    banner_products = models.ManyToManyField(SellerProduct, related_name='BANNER_AND_PRODUCTS')

    identifier = models.CharField(db_column='IDENTIFIER', max_length=100, blank=True, null=True)

    is_active = models.BooleanField(db_column='IS_ACTIVE', default=True)  # Field name made lowercase.

    class Meta:
        """
        class meta
        """
        db_table = 'TRANS_CUSTOMERS_BANNER_AND_PRODUCTS'
        app_label = 'customers'
        # unique_together = [('proposal_id', 'rfq_no')]


reversion.register(BannerAndProducts)
