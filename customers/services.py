import json
from rest_framework import status
from rest_framework.response import Response
from datetime import datetime
import reversion
from django.db import transaction
from Masters.models.ProductCategory import ProductCategory
from Masters.models.ProductSubCategory import ProductSubCategory
from Masters.models.ProductSubSubCategory import ProductSubSubCategory
from Sellers.models.ProductVariation import SellerProductVariation
from Sellers.models.SellerProduct import SellerProduct
from customers.models.Cart import CustomerCart
from customers.models.Customers import Customers
from customers.logger import customer_log, customer_wishlist_log, customer_cart_log
from customers.models.Wishlist import CustomerWishlist

from customers.serializers import CategoriesSerializer, SubCategoriesSerializer, \
    SubSubCategoriesSerializer, ProductListSerializer, ProductDetailSerializer, WishlistSerializer, \
        AllWishlistSerializer, CartSerializer, AllCartSerializer

class CategoriesService():
    
    def get_categories(self, request, ip):
        active_categories = ProductCategory.objects.filter(is_active=True)
        serial = CategoriesSerializer(active_categories, many=True)
        return Response({'msg':'Success','data':serial.data, 'status':1}, status=status.HTTP_200_OK)

    def get_sub_categories(self, request, ip, category_id):
        active_sub_categories = ProductSubCategory.objects.filter(is_active=True, product_id= category_id)
        serial = SubCategoriesSerializer(active_sub_categories, many=True)
        return Response({'msg':'Success','data':serial.data, 'status':1}, status=status.HTTP_200_OK)

    def get_sub_sub_categories(self, request, ip, category_id, sub_category_id):
        active_sub_sub_categories = ProductSubSubCategory.objects.filter(is_active=True, product_id= category_id, product_sub_category_id= sub_category_id)
        serial = SubSubCategoriesSerializer(active_sub_sub_categories, many=True)
        return Response({'msg':'Success','data':serial.data, 'status':1}, status=status.HTTP_200_OK)

class ProductService():

    def get_product_list(self, request, ip, category_id, sub_category_id, sub_sub_category_id):
        active_products = SellerProduct.objects.filter(is_active=True, category_id= category_id, 
        sub_category_id= sub_category_id, sub_sub_category_id= sub_sub_category_id)
        serial = ProductListSerializer(active_products, many=True, context={'request': request})
        return Response({'msg':'Success','data':serial.data, 'status':1}, status=status.HTTP_200_OK)

    def get_product_details(self, request, ip, product_uid):
        product_obj = SellerProduct.objects.get(product_uid= product_uid)
        serial = ProductDetailSerializer(product_obj, context={'request': request})
        return Response({'msg':'Success','data':serial.data, 'status':1}, status=status.HTTP_200_OK)

class Wishlist():

    def add_to_wishlist(self, request,ip, customer_uuid, product_uid):       

        data= {"customer_uuid":customer_uuid, "product_uid":product_uid}

        serial = WishlistSerializer(data=data, context={'request': request})

        try:
            if serial.is_valid(raise_exception=True):
                with transaction.atomic(), reversion.create_revision():
                    reversion.set_user(request.user)
                    reversion.set_comment(request.method)
                    reversion.set_date_created(
                        date_created=datetime.now())
                    customer_wishlist_obj = serial.save()
                    print(customer_wishlist_obj, serial.data)
                    customer_wishlist_log.info(f'Product is added to wishlist -- {customer_wishlist_obj.pk} -- {serial.data} -- {ip}')

                    # return serial.data
                    return Response({"msg": "Product is added to wishlist Succesfully",
                                        "data": serial.data, 'status' : 1}, status=status.HTTP_201_CREATED)

        except Exception as e:
            raise e
    

    def get_customer_wishlist(self, request, ip, customer_uuid):
        all_wishlist = CustomerWishlist.objects.filter(customer_id__cust_uuid=customer_uuid)
        serial = AllWishlistSerializer(all_wishlist, many=True, context={'request': request})
        return Response({'msg':'Success','data':serial.data, 'status':1}, status=status.HTTP_200_OK)


    def delete_from_wishlist(self, request,ip, wishlist_id):
 
        try:
            CustomerWishlist.objects.get(id=wishlist_id).delete()

            return Response({"msg": "Wishlist object deleted successfully",
                                        "data": {}, 'status' : 1}, status=status.HTTP_200_OK)
        
        except Exception as e:
            raise e

class Cart():

    def add_to_cart(self, request,ip):

        data= request.data
        serial = CartSerializer(data=data, context={'request': request})

        try:
            if serial.is_valid(raise_exception=True):
                with transaction.atomic(), reversion.create_revision():
                    reversion.set_user(request.user)
                    reversion.set_comment(request.method)
                    reversion.set_date_created(
                        date_created=datetime.now())
                    customer_cart_obj = serial.save()
                    print(customer_cart_obj, serial.data)
                    customer_cart_log.info(f'Product is added to cartt -- {customer_cart_obj.pk} -- {serial.data} -- {ip}')

                    # return serial.data
                    return Response({"msg": "Product is added to cart Succesfully",
                                        "data": serial.data, 'status' : 1}, status=status.HTTP_201_CREATED)

        except Exception as e:
            raise e
    

    def get_cart_list(self, request, ip, customer_uuid):
        all_cart = CustomerCart.objects.filter(customer_id__cust_uuid=customer_uuid)
        serial = AllCartSerializer(all_cart, many=True, context={'request': request})
        return Response({'msg':'Success','data':serial.data, 'status':1}, status=status.HTTP_200_OK)


    def update_customer_cart(self, request, ip):
        
        data= request.data
        cart_id= data.get('id')
        cart_obj= CustomerCart.objects.get(id=cart_id)
        serial = CartSerializer(cart_obj, data=data, context={'request': request}, partial=True)

        if serial.is_valid(raise_exception=True):
                with transaction.atomic(), reversion.create_revision():
                    reversion.set_user(request.user)
                    reversion.set_comment(request.method)
                    reversion.set_date_created(
                        date_created=datetime.now())
                    customer_cart_obj = serial.save()
                    customer_cart_log.info(f'Customer cart object updated -- {customer_cart_obj.pk} -- {serial.data} -- {ip}')

                    # return serial.data
                    return Response({"msg": "Customer cart object updated Succesfully",
                                        "data": serial.data, 'status' : 1}, status=status.HTTP_200_OK)


    def delete_from_cart(self, request,ip, cart_id):
 
        try:
            CustomerCart.objects.get(id=cart_id).delete()

            return Response({"msg": "Cart object deleted successfully",
                                        "data": {}, 'status' : 1}, status=status.HTTP_200_OK)
        
        except Exception as e:
            raise e