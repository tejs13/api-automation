"""
Model for qcs request
"""
from django.db import models
from reversion import revisions as reversion

from Masters.models.ProductSubSubCategory import ProductSubSubCategory
from Sellers.models.SellerProduct import SellerProduct
from Sellers.models.SellerBrand import SellerBrand
from commons.models import BaseModel
from customers.models.BannerAndProducts import BannerAndProducts


class CustomerHomescreen(BaseModel):
    top_sub_cats = models.ManyToManyField(ProductSubSubCategory, related_name='CUSTOMER_HOME_SCREEN')

    header_banner = models.ForeignKey(BannerAndProducts, on_delete=models.DO_NOTHING, db_column='HEADER_BANNER',
                                      related_name='CUSTOMER_HOMESCREENS_HEADER_BANNER')
    mid_banner = models.ForeignKey(BannerAndProducts, on_delete=models.DO_NOTHING, db_column='MID_BANNER',
                                      related_name='CUSTOMER_HOMESCREENS_MID_BANNER', blank=True, null=True)

    footer_banner = models.ForeignKey(BannerAndProducts, on_delete=models.DO_NOTHING, db_column='FOOTER_BANNER',
                                      related_name='CUSTOMER_HOMESCREENS_FOOTER_BANNER', blank=True, null=True)

    top_brands = models.ManyToManyField(SellerBrand, related_name='CUSTOMER_HOMESCREENS')

    featured_products = models.ManyToManyField(SellerProduct, related_name='CUSTOMER_HOMESCREENS_FEATURED')

    trending_products = models.ManyToManyField(SellerProduct, related_name='CUSTOMER_HOMESCREENS_TRENDING')

    is_active = models.BooleanField(db_column='IS_ACTIVE', default=True)
    class Meta:
        """
        class meta
        """
        db_table = 'TRANS_CUSTOMERS_HOMESCREEN'
        app_label = 'customers'
        # unique_together = [('proposal_id', 'rfq_no')]


reversion.register(CustomerHomescreen)
