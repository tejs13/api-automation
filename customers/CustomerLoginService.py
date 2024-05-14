import base64
from datetime import datetime

import pyotp
import reversion
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import status
from rest_framework.response import Response

from customers.logger import customer_log
from customers.models.DraftCustomer import DraftCustomer
from customers.models.Customers import Customers
from customers.serializers import CustomerRegisterSerializer


class CustomerOTPService:

    def generate_draft_cust_otp(self, request, ip):
        try:
            data = request.data
            print(data, "-------------")
            phone_no = data.get('phone')
            c_code = data.get('c_code')
            # check if seller already exists

            if Customers.objects.filter(phone_number=phone_no).exists():
                # generate OTP and store in Customer Obj

                cust_obj = Customers.objects.get(phone_number=phone_no)
                # TODO integrate OTP service
                cust_obj.phone_number = phone_no
                cust_obj.save()
                return Response({"msg": 'Customer Exists, OTP Sent', 'data' : {}, 'status' : 1}, status=status.HTTP_201_CREATED)

            else:
                is_d_customer_exist = DraftCustomer.objects.filter(phone_number=phone_no).exists()
                if is_d_customer_exist:
                    # just to call post save signal with .save()
                    d_customer = DraftCustomer.objects.get(phone_number=phone_no)
                    d_customer.phone_number = phone_no
                    d_customer.save()
                else:
                    d_customer = DraftCustomer.objects.create(phone_number=phone_no, country_code_id=c_code)

                return Response({"msg": 'Draft Created And OTP Sent', 'data' : {}, 'status' : 1}, status=status.HTTP_201_CREATED)
        except Exception as e:
            raise e

    def verify_cust_otp(self, request, ip):
        try:
            data = request.data
            print(data, "----------")
            phone_no = data.get('phone_no')
            country_code = data.get("c_code")
            otp = data.get('otp')
            is_registered_cust_exists = Customers.objects.filter(phone_number=phone_no).exists()

            # try getting registered customers first
            if is_registered_cust_exists:

                # TODO verify OTP from Customer obj and login the customer and send session
                # then verify OTP from Customer model field otp_generated
                cust_obj = Customers.objects.get(phone_number=phone_no)
                the_otp = cust_obj.otp_generated
                # TODO verify this OTP with service and login the customer
                user = User.objects.get(username=cust_obj.phone_number)
                print(user, "$$$$$$$$$$$$$")

                if user:
                    login(request, user)
                    # token, created = Token.objects.get_or_create(user=user)
                    # TODO : return the Customer info from GET Serilizer
                    return Response({'msg': 'Login Success', 'data': {}, 'status':1}, status=status.HTTP_200_OK)
                else:
                    return Response({"msg": "Authentication failed please Check Credetials !",
                                     'data': {}, 'status': 0},
                                    status=status.HTTP_400_BAD_REQUEST)


            else:
                # verofy OTP from DraftCustomer and upon succesfull, register Customer
                is_d_cust_exist = DraftCustomer.objects.filter(phone_number=phone_no).exists()
                if not is_d_cust_exist:
                    raise Exception(f"No Phone No -- {phone_no} Exists For OTP ")

                d_cust_obj = DraftCustomer.objects.get(phone_number=phone_no)
                data = {
                    "phone_number": d_cust_obj.phone_number,
                    "country_code": country_code
                }

                # totp_obj = pyotp.TOTP(base64.b32encode(email.lower().encode()))
                # is_otp_verified = totp_obj.verify(str(otp))
                # TODO  temp for DEV, always true
                is_otp_verified = True
                print("OTP VERIFICATION ===========", is_otp_verified)

                if is_otp_verified:
                    # if OTP verification success, create customer object
                    created_seller_details = self.register_customer(request, ip, data)
                    # TODO login the created customer and send session
                    return Response({"msg": "OTP Verification Success",
                                     'is_otp_verified': True,
                                     'data': {}, 'status' : 1},
                                    status=status.HTTP_200_OK)
                else:
                    return Response({"msg": "OTP Verification Failed !",
                                     'is_otp_verified': False,
                                     'data': {'phone_no': d_cust_obj.phone_number},
                                     'status' : 0},
                                    status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            raise e


    def register_customer(self, request, ip, obj_data):
        # data = json.loads(request.data.get('data'))
        # data = request.data
        print(obj_data, "********************")
        serial = CustomerRegisterSerializer(data=obj_data, context={'request': request})
        try:

            if serial.is_valid(raise_exception=True):
                with transaction.atomic(), reversion.create_revision():
                    reversion.set_user(request.user)
                    reversion.set_comment(request.method)
                    reversion.set_date_created(
                        date_created=datetime.now())
                    seller_obj = serial.save()
                    print(seller_obj, serial.data)
                    customer_log.info(f'CUSTOMER object saved -- {seller_obj.pk} -- {serial.data} -- {ip}')
                    # start the Approval Workflow here
                    # if 'sellers' in WORKFLOW_MODEL_LIST:
                    #     trigger_workflow(request, seller_obj, 'initiated', 'Sellers', 'sellers', 'Init')


                    # seller_details = SellerDetailsSerializer(seller_obj)
                    # return seller_details
                    return Response({"msg": "Customer Created Succesfully",
                                     "data": {}, 'status': 1}, status=status.HTTP_201_CREATED)

        except Exception as e:
            raise e


    def login_customer_generate_otp(self, request, ip, phone_no):
        pass



