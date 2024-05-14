from django.contrib import admin

from customers.models.BannerAndProducts import BannerAndProducts
from customers.models.HomeScreen import CustomerHomescreen
from customers.models.Customers import Customers
from customers.models.DraftCustomer import DraftCustomer
from customers.models.Wishlist import CustomerWishlist
from customers.models.Cart import CustomerCart

admin.site.register(CustomerHomescreen)
admin.site.register(BannerAndProducts)
admin.site.register(Customers)
admin.site.register(CustomerWishlist)
admin.site.register(CustomerCart)


