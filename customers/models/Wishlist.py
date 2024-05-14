"""
Model for qcs request
"""

from django.db import models
from reversion import revisions as reversion

from Sellers.models.SellerProduct import SellerProduct
from commons.models import BaseModel
from customers.models.Customers import Customers


class CustomerWishlist(BaseModel):
    customer_id= models.ForeignKey(Customers, on_delete=models.CASCADE, related_name='CUSTOMER_WISHLIST', db_column='CUSTOMER_ID')
    product_id= models.ForeignKey(SellerProduct, on_delete=models.CASCADE, related_name='CUSTOMER_WISHLIST', db_column='PRODUCT_ID')


    def __str__(self):
        return str(self.id) + '--' + str(self.customer_id) + '--' + str(self.product_id)

    class Meta:
        """
        class meta
        """
        db_table = 'TRANS_CUSTOMER_WISHLIST'
        app_label = 'customers'
        unique_together = [('customer_id', 'product_id')]


reversion.register(CustomerWishlist)