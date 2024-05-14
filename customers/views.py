from django.shortcuts import render

# Create your views here.
from rest_framework import views, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from commons.utils import get_client_ip
from customers.CustomerHomeScreenService import HomeScreenService
from customers.services import CategoriesService, ProductService, Wishlist, Cart
from customers.logger import customer_log, customer_wishlist_log, customer_cart_log
from customers.CustomerLoginService import CustomerOTPService
from nyeon.base_service import CustomAuthentication


class GenerateCustomerOTPView(views.APIView):
    authentication_classes = [CustomAuthentication]
    permission_classes = [IsAuthenticated]  # ,IsAuthorized]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request, *args, **kwargs):
        ip = get_client_ip(request)
        generate_cust_otp = CustomerOTPService()
        try:
            res = generate_cust_otp.generate_draft_cust_otp(request, ip)
            customer_log.info(f'Post clarification view success -- ip {ip} -- response -- {res}')
            return res

        except Exception as e:
            customer_log.exception(e)
            return Response({'msg': str(e), 'data': {}, 'status': 0}, status=status.HTTP_400_BAD_REQUEST)



class VerifyOTPView(views.APIView):
    authentication_classes = [CustomAuthentication]
    permission_classes = [IsAuthenticated]  # ,IsAuthorized]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request, *args, **kwargs):
        ip = get_client_ip(request)
        cust_otp_service = CustomerOTPService()
        try:
            res = cust_otp_service.verify_cust_otp(request, ip)
            customer_log.info(f'Post clarification view success -- ip {ip} -- response -- {res}')
            return res

        except Exception as e:
            customer_log.exception(e)
            return Response({'msg': str(e), 'data': {}, 'status': 0}, status=status.HTTP_400_BAD_REQUEST)



class HomeScreenView(views.APIView):
    authentication_classes = [CustomAuthentication]
    permission_classes = [IsAuthenticated]  # ,IsAuthorized]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request, *args, **kwargs):
        ip = get_client_ip(request)
        cust_home_service = HomeScreenService()
        try:
            res = cust_home_service.get_home_screen(request, ip)
            customer_log.info(f'Post clarification view success -- ip {ip} -- response -- {res}')
            return res

        except Exception as e:
            customer_log.exception(e)
            return Response({'msg': str(e), 'data': {}, 'status': 0}, status=status.HTTP_400_BAD_REQUEST)


class GetCategoriesView(views.APIView):
    authentication_classes = [CustomAuthentication]
    permission_classes = [IsAuthenticated]  # ,IsAuthorized]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request, *args, **kwargs):
        ip = get_client_ip(request)
        categories_service = CategoriesService()
        try:
            res = categories_service.get_categories(request, ip)
            customer_log.info(f'Post clarification view success -- ip {ip} -- response -- {res}')
            return res

        except Exception as e:
            customer_log.exception(e)
            return Response({'msg': str(e), 'data': {}, 'status': 0}, status=status.HTTP_400_BAD_REQUEST)


class GetSubCategoriesView(views.APIView):
    authentication_classes = [CustomAuthentication]
    permission_classes = [IsAuthenticated]  # ,IsAuthorized]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request, *args, **kwargs):
        ip = get_client_ip(request)
        categories_service = CategoriesService()

        try:
            category_id= self.request.query_params.get("category_id", None)
            if not category_id:
                raise Exception("Product Category ID None Exception Raised")

            res = categories_service.get_sub_categories(request, ip, category_id)
            customer_log.info(f'Post clarification view success -- ip {ip} -- response -- {res}')
            return res

        except Exception as e:
            customer_log.exception(e)
            return Response({'msg': str(e), 'data': {}, 'status': 0}, status=status.HTTP_400_BAD_REQUEST)

class GetSubSubCategoriesView(views.APIView):
    authentication_classes = [CustomAuthentication]
    permission_classes = [IsAuthenticated]  # ,IsAuthorized]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request, *args, **kwargs):
        ip = get_client_ip(request)
        categories_service = CategoriesService()

        try:
            category_id= self.request.query_params.get("category_id", None)
            if not category_id:
                raise Exception("Product Category ID None Exception Raised")

            sub_category_id= self.request.query_params.get("sub_category_id", None)
            if not sub_category_id:
                raise Exception("Product Sub Category ID None Exception Raised")

            res = categories_service.get_sub_sub_categories(request, ip, category_id, sub_category_id)
            customer_log.info(f'Post clarification view success -- ip {ip} -- response -- {res}')
            return res

        except Exception as e:
            customer_log.exception(e)
            return Response({'msg': str(e), 'data': {}, 'status': 0}, status=status.HTTP_400_BAD_REQUEST)

class GetProductListView(views.APIView):
    authentication_classes = [CustomAuthentication]
    permission_classes = [IsAuthenticated]  # ,IsAuthorized]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request, *args, **kwargs):
        ip = get_client_ip(request)
        product_service = ProductService()

        try:
            category_id= self.request.query_params.get("category_id", None)
            if not category_id:
                raise Exception("Product Category ID None Exception Raised")

            sub_category_id= self.request.query_params.get("sub_category_id", None)
            if not sub_category_id:
                raise Exception("Product Sub Category ID None Exception Raised")

            sub_sub_category_id= self.request.query_params.get("sub_sub_category_id", None)
            if not sub_sub_category_id:
                raise Exception("Product Sub Sub Category ID None Exception Raised")

            res = product_service.get_product_list(request, ip, category_id, 
            sub_category_id, sub_sub_category_id)
            customer_log.info(f'Post clarification view success -- ip {ip} -- response -- {res}')
            return res

        except Exception as e:
            customer_log.exception(e)
            return Response({'msg': str(e), 'data': {}, 'status': 0}, status=status.HTTP_400_BAD_REQUEST)

class GetProductDetailsView(views.APIView):
    authentication_classes = [CustomAuthentication]
    permission_classes = [IsAuthenticated]  # ,IsAuthorized]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request, *args, **kwargs):
        ip = get_client_ip(request)
        product_details = ProductService()
        try:
            product_uid= kwargs.get('product_uid', None)
            if not product_uid:
                raise Exception("Product UID None Exception Raised")

            res = product_details.get_product_details(request, ip, product_uid)
            customer_log.info(f'Post clarification view success -- ip {ip} -- response -- {res}')
            return res

        except Exception as e:
            customer_log.exception(e)
            return Response({'msg': str(e), 'data': {}, 'status': 0}, status=status.HTTP_400_BAD_REQUEST)

class WishlistView(views.APIView):
    authentication_classes = [CustomAuthentication]
    permission_classes = [IsAuthenticated]  # ,IsAuthorized]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request, *args, **kwargs):
        ip = get_client_ip(request)
        customer_wishlist_service = Wishlist()

        try:
            customer_uuid = kwargs.get('customer_uuid', None)
            if not customer_uuid:
                raise Exception("UUID None Exception Raised")
            
            product_uid = kwargs.get('product_uid', None)
            if not product_uid:
                raise Exception("Product UID None Exception Raised")

            res = customer_wishlist_service.add_to_wishlist(request, ip, customer_uuid, product_uid)

            customer_wishlist_log.info(f'Post clarification view success -- ip {ip} -- response -- {res}')
            return res

        except Exception as e:
            customer_wishlist_log.exception(e)
            return Response({'msg': str(e), 'data':{}, 'status':0}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        ip = get_client_ip(request)
        customer_wishlist_service = Wishlist()

        try:
            customer_uuid = kwargs.get('customer_uuid', None)
            if not customer_uuid:
                raise Exception("UUID None Exception Raised")

            res = customer_wishlist_service.get_customer_wishlist(request, ip, customer_uuid)
            customer_wishlist_log.info(f'Post clarification view success -- ip {ip} -- response -- {res}')
            return res

        except Exception as e:
            customer_wishlist_log.exception(e)
            return Response({'msg': str(e), 'data': {}, 'status': 0}, status=status.HTTP_400_BAD_REQUEST)

    
    def delete(self, request, *args, **kwargs):
        ip = get_client_ip(request)
        customer_wishlist_service = Wishlist()

        try:
            wishlist_id = kwargs.get('wishlist_id', None)
            if not wishlist_id:
                raise Exception("Wishlist ID None Exception Raised")

            res = customer_wishlist_service.delete_from_wishlist(request, ip, wishlist_id)

            customer_wishlist_log.info(f'Post clarification view success -- ip {ip} -- response -- {res}')
            return res

        except Exception as e:
            customer_wishlist_log.exception(e)
            return Response({'msg': str(e), 'data':{}, 'status':0}, status=status.HTTP_400_BAD_REQUEST)


class CartView(views.APIView):
    authentication_classes = [CustomAuthentication]
    permission_classes = [IsAuthenticated]  # ,IsAuthorized]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request, *args, **kwargs):
        ip = get_client_ip(request)
        customer_cart_service = Cart()

        try:
  
            res = customer_cart_service.add_to_cart(request, ip)

            customer_cart_log.info(f'Post clarification view success -- ip {ip} -- response -- {res}')
            return res

        except Exception as e:
            customer_cart_log.exception(e)
            return Response({'msg': str(e), 'data':{}, 'status':0}, status=status.HTTP_400_BAD_REQUEST)


    def get(self, request, *args, **kwargs):
        ip = get_client_ip(request)
        customer_cart_service = Cart()

        try:
            customer_uuid = kwargs.get('customer_uuid', None)
            if not customer_uuid:
                raise Exception("UUID None Exception Raised")

            res = customer_cart_service.get_cart_list(request, ip, customer_uuid)
            customer_cart_log.info(f'Post clarification view success -- ip {ip} -- response -- {res}')
            return res

        except Exception as e:
            customer_cart_log.exception(e)
            return Response({'msg': str(e), 'data': {}, 'status': 0}, status=status.HTTP_400_BAD_REQUEST)

    
    def put(self, request, *args, **kwargs):
        ip = get_client_ip(request)
        seller_cart_service = Cart()
        try:
            # customer_cart_id = kwargs.get('customer_cart_id', None)
            # if not customer_cart_id:
            #     raise Exception("Cart ID None Exception Raised")

            res = seller_cart_service.update_customer_cart(request, ip)
            customer_cart_log.info(f'Post clarification view success -- ip {ip} -- response -- {res}')
            return res

        except Exception as e:
            customer_cart_log.exception(e)
            return Response({'msg': str(e), 'data':{}, 'status':0}, status=status.HTTP_400_BAD_REQUEST)

    
    def delete(self, request, *args, **kwargs):
        ip = get_client_ip(request)
        customer_cart_service = Cart()

        try:
            cart_id = kwargs.get('cart_id', None)
            if not cart_id:
                raise Exception("Cart ID None Exception Raised")

            res = customer_cart_service.delete_from_cart(request, ip, cart_id)

            customer_cart_log.info(f'Post clarification view success -- ip {ip} -- response -- {res}')
            return res

        except Exception as e:
            customer_cart_log.exception(e)
            return Response({'msg': str(e), 'data':{}, 'status':0}, status=status.HTTP_400_BAD_REQUEST)
