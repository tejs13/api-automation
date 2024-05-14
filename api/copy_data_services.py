"""
Service Layer
"""

from rest_framework import status
import datetime
import traceback
from copy import deepcopy
from django.db import transaction, IntegrityError
from reversion import revisions as reversion
from api.logger_directory import requests_logger
from rest_framework.response import Response
from django.http.response import JsonResponse
from django.apps import apps
from rest_framework.parsers import JSONParser
from api.serializers import ExcelSerializer
import json

API_LOG = requests_logger()

class CopyDataService:
    """
    Service Class
    """

    def clone_model_object(self,request,to_copy):
        """
        Purpose: To deep copy object from from_queryset
        :param request: Request object
        :type request: Request Object
        :param kwargs: Request object,queryset for deep copy
        :return: Deep copy object with the updated creation details.
        """

        to_copy.created_date = datetime.datetime.now()
        to_copy.created_by = request.user.username
        to_copy.last_updated_by= request.user.username
        to_copy.last_updated_date = datetime.datetime.now()
        return to_copy


    @transaction.atomic
    def copy_data(self,request,app, model):
        """
        Purpose: To copy object based on filtered from_data to provided to_data.
        :param request: Request object
        :param app:the app name coming from decorator
        :param model:the model name coming from decorator
        :return: response after saving the serialized object which is copied from from_data.
        """


        try:

            from_data = dict(request.data.get('from'))
            from_data["is_deleted"]=False
            to_data= dict(request.data.get('to'))
            to_object=request.data.get('to')
            model_obj = apps.get_model(app, model)
            serialize = ExcelSerializer(model_obj, {})
            from_queryset=model_obj.objects.filter(**from_data)
            to_queryset=model_obj.objects.filter(**to_data)
            primary_key_field = [field.name for field in model_obj._meta.get_fields() if field.primary_key]
            existing_data_ids=[]
            for obj in to_queryset:
                if  to_queryset!=None:
                    existing_data_ids.append(obj.pk)

            for obj in from_queryset:
                print(obj)
                to_copy=deepcopy(obj)
                if existing_data_ids:
                    to_copy.id=existing_data_ids[0]
                else:
                    to_copy.id = None
                to_copy=self.clone_model_object(request,to_copy)
                for k,v in to_object.items():
                    setattr(to_copy, k, v)

                serialized_data = serialize(to_copy).data
                if serialized_data[primary_key_field[0]]:
                    instance = model_obj.objects.get(pk=serialized_data[primary_key_field[0]])
                    serialize_object = serialize(instance, data=serialized_data, partial=True)
                else:
                    serialize_object = serialize(data=serialized_data)

                with reversion.create_revision():
                    if serialize_object.is_valid():
                        # createObj=reversion_post(request,serialize_object)
                        reversion.set_user(request.user)
                        reversion.set_comment(request.method)
                        reversion.set_date_created(date_created=datetime.datetime.now())
                        createdObj = serialize_object.save()
                        response = Response(serialize_object.data, status=status.HTTP_200_OK)
                    else:
                        response = Response(serialize_object.errors, status=status.HTTP_400_BAD_REQUEST)

            return response

        except Exception as exc:
            full_traceback = traceback.format_exc()
            API_LOG.error(full_traceback)
            return Response({}, status=status.HTTP_400_BAD_REQUEST)

    def get_data_for_copy(self,request,app,model):
        """
        Purpose:To get the field's data based on field provided as querystring
        :param request:the request object
        :param app:the app name coming from decorator
        :param model:the model name coming from decorator
        :return:Response after getting value_list of provided field.
        """
        try:

            model_obj = apps.get_model(app, model)
            field =request.query_params.get("field")
            data = model_obj.objects.values_list(field,flat=True).distinct()
            return Response(data, status=status.HTTP_200_OK)
        except Exception as exc:
            full_traceback = traceback.format_exc()
            API_LOG.error(full_traceback)
            return Response({}, status=status.HTTP_204_NO_CONTENT)

















