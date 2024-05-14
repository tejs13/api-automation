import os
import pandas as pd
import pika
import json
from django.conf import settings
from django.apps import apps
from django.http import HttpResponse
from django.utils.module_loading import import_string
from rest_framework import status
from rest_framework.response import Response

from api.check_fields import check_fields
from api.filters import handleFilterData, handleSearchData
from api.utils import retrieve_correct_app
from api.workflow_validators import get_pending_for_group_user

WORKFLOW_MODEL_LIST = settings.__dict__['_wrapped'].__dict__['WORKFLOW_MODEL_LIST']
TRANS_FILTER_QS_SERIALIZER = settings.__dict__['_wrapped'].__dict__['TRANS_FILTER_QS_SERIALIZER']
EXCEL_EXPORT_CONFIGS = settings.__dict__['_wrapped'].__dict__['EXCEL_EXPORT_CONFIGS']
RABBITMQ_CONF = settings.__dict__['_wrapped'].__dict__['RABBITMQ_CONF']

class DashBoardService():

    def get_models_summary(self, models_data):
        data = []
        for model in models_data:
            info = {}
            model_obj = apps.get_model(model['related_app'], model['model'])
            if model['model'].lower() in WORKFLOW_MODEL_LIST:
                info['model'] = model['title']
                info['total'] = model_obj.objects.filter(is_active=True, is_deleted=False).count()
                info['approved'] = model_obj.objects.filter(is_active=True, is_deleted=False, is_approved=True, status__iexact='Approved').count()
                info['pending'] = model_obj.objects.filter(is_active=True, is_deleted=False, is_approved=False,).exclude(status__iexact='Approved').count()
                info['rejected'] = model_obj.objects.filter(is_active=True, is_deleted=False, is_approved=True, status__iexact='Rejected').count()
                info['in_workflow'] = True
                data.append(info)
            else:
                info['model'] = model['title']
                info['in_workflow'] = False
                info['total'] = model_obj.objects.filter(is_active=True, is_deleted=False).count()
                data.append(info)

        return Response(data, status=status.HTTP_200_OK)


class ExcelExportService:

    def generate_bulk_excel_and_mail(self, serial_data, request, model):
        body={
            "serial_data": serial_data,
            "model":model,
            "request_user_email": request.user.email,
            "EXCEL_EXPORT_CONFIGS":EXCEL_EXPORT_CONFIGS,
            "EXCEL_EXPORT_DIR":settings.EXCEL_EXPORT_DIR,
            "BASE_DIR":settings.BASE_DIR,
            "RABBITMQ_CONF":RABBITMQ_CONF,
        }
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_CONF['RABBITMQ_CON_URL']))
        channel = connection.channel()
        channel.queue_declare(queue=RABBITMQ_CONF['EXCEL_EXPORT_QUEUE'])
        channel.basic_publish(exchange='', routing_key=RABBITMQ_CONF['EXCEL_EXPORT_QUEUE'], body=json.dumps(body))
        connection.close()
        return Response(status=204)

    def generate_excel_and_response(self, serial_data, request,  app, model):
        excel = pd.json_normalize(serial_data)
        if model.lower() in EXCEL_EXPORT_CONFIGS:
            excel.drop(EXCEL_EXPORT_CONFIGS[model.lower()]['fields_to_exclude'], axis=1, errors='ignore', inplace=True)
        excel.columns = excel.columns.str.strip()
        excel.columns = excel.columns.str.replace('_', ' ')
        excel.columns = map(str.upper, excel.columns)
        path = os.path.join(settings.BASE_DIR, f'{model}.xlsx')
        excel.to_excel(path,index=False)
        with open(path, 'rb') as f:
            file = f.readlines()
        os.remove(path)
        return HttpResponse(file, content_type='application/ms-excel')

    def export(self, pks, request, app, model):
        app, model_obj = retrieve_correct_app(model)
        if not request.GET._mutable:
            request.GET._mutable = True

        if request.data.get("results") == "all" and pks == 'all':
            request.GET['excel'] = 'true'
            request.GET['page'] = 1
            if request.data.get("filter"):
                request.GET['filter'] = 1
                filters = request.data.get("filter").split('&')
                for f in filters:
                    request.GET[f.split('=')[0]] = f.split('=')[1]
                qs = handleFilterData(request, app, model, 1, 10000000, return_qs=True)
            elif request.data.get("search"):
                filters = request.data.get("search").split('=')
                request.GET['search'] = filters[1]
                qs = handleSearchData(app, model, request, 1, 10000000, return_qs=True)
            else:
                if app + '.' + model.lower() in TRANS_FILTER_QS_SERIALIZER:
                    qs_function = import_string(TRANS_FILTER_QS_SERIALIZER[app + '.' + model.lower()][0])
                    qs = qs_function(request)
                else:
                    if model.lower() in WORKFLOW_MODEL_LIST:
                        qs = get_pending_for_group_user(model_obj, request)
                    else:
                        qs = model_obj.objects.filter(is_deleted=False).order_by('-pk')
        else:
            qs = model_obj.objects.filter(pk__in=pks)

        modelSerializer = import_string(TRANS_FILTER_QS_SERIALIZER[app + '.' + model.lower()][1]) \
            if app + '.' + model.lower() in TRANS_FILTER_QS_SERIALIZER else check_fields(model_obj)
        serial = modelSerializer(qs, many=True,  context={"request": request, "group": None}).data
        serial_data = list(serial)
        if serial_data.__len__() >= 1000:
            return self.generate_bulk_excel_and_mail(serial_data, request, model)
        else:
            return self.generate_excel_and_response(serial_data, request, app, model)





