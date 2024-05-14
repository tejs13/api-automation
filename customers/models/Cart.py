"""
Model for qcs request
"""

from django.db import models
from reversion import revisions as reversion

from Sellers.models.ProductVariation import SellerProductVariation
from commons.models import BaseModel
from customers.models.Customers import Customers


class CustomerCart(BaseModel):
    customer_id= models.ForeignKey(Customers, on_delete=models.CASCADE, related_name='CUSTOMER_CART', db_column='CUSTOMER_ID')
    product_variation_id= models.ForeignKey(SellerProductVariation, on_delete=models.CASCADE, related_name='CUSTOMER_CART', db_column='PRODUCT_VARIATION_ID')
    quantity= models.PositiveIntegerField()

    def __str__(self):
        return str(self.id) + '--' + str(self.customer_id) + '--' + str(self.product_variation_id)

    class Meta:
        """
        class meta
        """
        db_table = 'TRANS_CUSTOMER_CART'
        app_label = 'customers'
        unique_together = [('customer_id', 'product_variation_id')]


reversion.register(CustomerCart)