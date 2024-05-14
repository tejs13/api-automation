from django.db.models import FileField

from api.workflow_validators import get_pending_for_group_user
from django_filters import rest_framework as custom_filters
from rest_framework import filters, status
from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import CharFilter, NumberFilter, \
    DateFromToRangeFilter, DateFilter
from django.utils.module_loading import import_string

from api.alias import AliasField
from api.check_fields import check_fields
from api.config_metadata import FILTER_FIELD_MAPPING
from api.decorators import REQ_LOGS
from api.utils import retrieve_correct_app
from commons.functions import get_paginated_queryset

APPLY_SEARCH_MODEL_FIELDS = settings.__dict__['_wrapped'].__dict__['APPLY_SEARCH_MODEL_FIELDS']
FOREIGN_KEY_UI_NAME_MAP = settings.__dict__['_wrapped'].__dict__['FOREIGN_KEY_UI_NAME_MAP']
TRANS_FILTER_QS_SERIALIZER = settings.__dict__['_wrapped'].__dict__['TRANS_FILTER_QS_SERIALIZER']
WORKFLOW_MODEL_LIST = settings.__dict__['_wrapped'].__dict__['WORKFLOW_MODEL_LIST']

def genericfilter(model_obj, filters_dict):

    class ModelFilter(custom_filters.FilterSet):
        locals().update(filters_dict)
        class Meta:
            model = model_obj
            fields = '__all__'
            filter_overrides = {
                AliasField: {
                    'filter_class': custom_filters.CharFilter,
                    'extra': lambda f: {
                        'lookup_expr': 'icontains',
                    }
                },
                FileField: {
                    'filter_class': custom_filters.CharFilter,
                    'extra': lambda f: {
                        'lookup_expr': 'icontains',
                    }
                },
            }
    return ModelFilter


def genericSearch(model):
    class DynamicSearchFilter(filters.SearchFilter):
        def get_search_fields(self, view, request):
            temp = request.GET.copy()
            if 'page' in temp:
                temp.pop('page')
            if 'pageSize' in temp:
                temp.pop('pageSize')
            if 'filter' in temp:
                temp.pop('filter')
            temp.setlist('search_fields',APPLY_SEARCH_MODEL_FIELDS[model.lower()])
            return temp.getlist('search_fields', [])

    return DynamicSearchFilter


def handleCombinationData(app, model, request, page, pageSize):
    try:
        if 'search' in request.GET:
            DynamicSearchFilter = genericSearch(model)
            model_filter = DynamicSearchFilter()
            app, model_obj = retrieve_correct_app(model)
            if app + '.' + model.lower() in TRANS_FILTER_QS_SERIALIZER:
                modelSerializer = import_string(TRANS_FILTER_QS_SERIALIZER[app + '.' + model.lower()][1])
            else:
                modelSerializer = check_fields(model_obj)
            filtered_qs = handleFilterData(request, app, model, page, pageSize, return_qs=True)
            final_qs = model_filter.filter_queryset(request, filtered_qs, APIView)
            paged_queryset = get_paginated_queryset(final_qs, pageSize, page)
            objs = paged_queryset.object_list
            serial = modelSerializer(objs, many=True, context={"request": request, "group": None})
            response = {
                "total": final_qs.count(),
                "results":  [i for i in serial.data if i is not None]
            }
            return Response(response, status=status.HTTP_200_OK)

    except Exception as e:
        REQ_LOGS.exception(e)
        return Response({'msg': str(e), 'data': {}, 'status': 0}, status=status.HTTP_400_BAD_REQUEST)

def handleSearchData(app, model, request, page, pageSize, return_qs=False):
    try:
        if app + '.' + model.lower() in TRANS_FILTER_QS_SERIALIZER:
            qs_function = import_string(TRANS_FILTER_QS_SERIALIZER[app + '.' + model.lower()][0])
            objs = qs_function(request)
            modelSerializer = import_string(TRANS_FILTER_QS_SERIALIZER[app + '.' + model.lower()][1])
        else:
            app, model_obj = retrieve_correct_app(model)
            if model.lower() in WORKFLOW_MODEL_LIST:
                objs = get_pending_for_group_user(model_obj, request)
            else:
                objs = model_obj.objects.filter(is_deleted=False).order_by('-pk')
            modelSerializer = check_fields(model_obj)

        DynamicSearchFilter = genericSearch(model)
        # model_obj = apps.get_model(app, model)
        model_filter = DynamicSearchFilter()
        final_qs = model_filter.filter_queryset(request, objs, APIView)
        if return_qs:
            return final_qs
        if 'excel' in request.query_params:
            pageSize = final_qs.count()
        paged_queryset = get_paginated_queryset(final_qs, pageSize, page)
        objs = paged_queryset.object_list
        serial = modelSerializer(objs, many=True, context={"request": request, "group": None})
        response = {
            "total": final_qs.count(),
            'msg' : 'Success',
            "data":  [i for i in serial.data if i is not None],
            'status' : 1

        }
        return Response(response, status=status.HTTP_200_OK)
    except Exception as e:
        REQ_LOGS.exception(e)
        return Response({'msg': str(e), 'data': {}, 'status': 0}, status=status.HTTP_400_BAD_REQUEST)

def handleFilterData(request, app, model, page, pageSize, return_qs=False):
    try:
        if request.GET.__len__() > 0:
            # model_obj = apps.get_model(app, model)
            app, model_obj = retrieve_correct_app(model)
            # query_dict = request.GET.dict()
            query_dict = dict(request.GET.lists())
            op_executed = False
            fk_executed = False
            if "page" in query_dict:
                query_dict.pop('page')
            if "pageSize" in query_dict:
                query_dict.pop('pageSize')
            if "filter" in query_dict:
                query_dict.pop('filter')
            if 'search' in query_dict:
                query_dict.pop('search')
            filter_dict = {}
            for i in list(query_dict.keys()):
                if ('.name' in i) or ('.' in i and '.name' not in i):
                    fk_executed = True
                    for dict_map in FOREIGN_KEY_UI_NAME_MAP[model.lower()][i.split('.')[0]]:
                        if (dict_map['type'] == 'integer' and i.split('.')[0] in dict_map['field'] and '.name' in i) \
                                or (dict_map['type'] == 'integer' and i.split('.')[1] in dict_map['field']):
                            if '_' in query_dict[i][0]:
                                values = query_dict[i][0].split('_')
                                op = values[0]
                                value = "_".join(values[1:])
                                del query_dict[i]
                                filter_dict[dict_map['field']] = NumberFilter(field_name=dict_map['field'],
                                                                              lookup_expr=op)
                                query_dict[dict_map['field']] = value
                                break
                            else:
                                filter_dict[dict_map['field']] = NumberFilter(lookup_expr='exact')
                                old_value = query_dict[i][0]
                                del query_dict[i]
                                i = dict_map['field']
                                query_dict[i] = old_value
                                break
                        if (dict_map['type'] == 'text' and i.split('.')[0] in dict_map['field'] and '.name' in i) \
                                or (dict_map['type'] == 'text' and i.split('.')[1] in dict_map['field']):
                            if '_' in query_dict[i][0]:
                                values = query_dict[i][0].split('_')
                                op = values[0]
                                value = "_".join(values[1:])
                                del query_dict[i]
                                filter_dict[dict_map['field']] = CharFilter(field_name=dict_map['field'],
                                                                            lookup_expr=op)
                                query_dict[dict_map['field']] = value
                                break
                            else:
                                filter_dict[dict_map['field']] = CharFilter(lookup_expr='iexact')
                                old_value = query_dict[i][0]
                                del query_dict[i]
                                i = dict_map['field']
                                query_dict[i] = old_value
                                break
                        if (dict_map['type'] == 'date' and i.split('.')[0] in dict_map['field'] and '.name' in i) \
                                or (dict_map['type'] == 'date' and i.split('.')[1] in dict_map['field']):
                            if '_' in query_dict[i][0]:
                                values = query_dict[i][0].split('_')
                                op = values[0]
                                value = "_".join(values[1:])
                                del query_dict[i]
                                filter_dict[dict_map['field']] = DateFromToRangeFilter()
                                if op == 'exact':
                                    filter_dict[dict_map['field']] = DateFilter(lookup_expr='date')
                                if query_dict[i].__len__() == 2:
                                    op1 = query_dict[i][0].split('_')[0]
                                    value_1 = query_dict[i][0].split('_')[1]
                                    op2 = query_dict[i][1].split('_')[0]
                                    value_2 = query_dict[i][1].split('_')[1]
                                    query_dict[dict_map['field'] + '_' + op1] = value_1
                                    query_dict[dict_map['field'] + '_' + op2] = value_2
                                else:
                                    query_dict[dict_map['field'] + '_' + op] = value
                                break
                            else:
                                values = query_dict[i][0].split('_')
                                op = values[0]
                                value = "_".join(values[1:])
                                filter_dict[dict_map['field']] = DateFromToRangeFilter()
                                del query_dict[i]
                                query_dict[dict_map['field'] + '_' + op] = value
                                if op == 'exact':
                                    filter_dict[dict_map['field']] = DateFilter(lookup_expr='date')
                                    query_dict[dict_map['field']] = value
                                break

                if i in query_dict:
                    if '_' in query_dict[i][0] and '.' not in i:
                        op_executed = True
                        values = query_dict[i][0].split('_')
                        op = values[0]
                        value = "_".join(values[1:])
                        if op in FILTER_FIELD_MAPPING['integer']:
                            filter_dict[i] = NumberFilter(field_name=i, lookup_expr=op)
                            query_dict[i] = value
                        elif op in FILTER_FIELD_MAPPING['text']:
                            filter_dict[i] = CharFilter(field_name=i, lookup_expr=op)
                            query_dict[i] = value
                        elif op in FILTER_FIELD_MAPPING['date']:
                            filter_dict[i] = DateFromToRangeFilter()
                            if query_dict[i].__len__() == 2:
                                op1 = query_dict[i][0].split('_')[0]
                                value_1 = query_dict[i][0].split('_')[1]
                                op2 = query_dict[i][1].split('_')[0]
                                value_2 = query_dict[i][1].split('_')[1]
                                query_dict[i + '_' + op1] = value_1
                                query_dict[i + '_' + op2] = value_2
                                del query_dict[i]
                            else:
                                query_dict[i + '_' + op] = value
                                if op == 'exact':
                                    filter_dict[i] = DateFilter(lookup_expr='date')

                if '.' not in i and not op_executed and not fk_executed:
                    query_dict[i] = query_dict[i][0]

            model_filter = genericfilter(model_obj, filter_dict)
            if app + '.' + model.lower() in TRANS_FILTER_QS_SERIALIZER:
                qs_function = import_string(TRANS_FILTER_QS_SERIALIZER[app + '.' + model.lower()][0])
                queryset = qs_function(request)
                modelSerializer = import_string(TRANS_FILTER_QS_SERIALIZER[app + '.' + model.lower()][1])
            else:
                if model.lower() in WORKFLOW_MODEL_LIST:
                    queryset = get_pending_for_group_user(model_obj, request)
                else:
                    queryset = model_obj.objects.filter(is_deleted=False).order_by('-pk')
                modelSerializer = check_fields(model_obj)

            f = model_filter(query_dict, queryset=queryset)
            if return_qs:
                return f.qs
            if 'excel' in request.query_params:
                pageSize = f.qs.count()
            paged_queryset = get_paginated_queryset(f.qs, pageSize, page)
            objs = paged_queryset.object_list
            serial = modelSerializer(objs, many=True, context={
                "request": request, "group": None})
            response = {
                "total": f.qs.count(),
                'msg' : 'Success',
                "data":  [i for i in serial.data if i is not None],
                'status' : 1
            }
            return Response(response, status=status.HTTP_200_OK)
        else:
            return Response({'msg': 'Error !', 'data': {}, 'status': 0}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        REQ_LOGS.exception(e)
        return Response({'msg': str(e), 'data': {}, 'status': 0}, status=status.HTTP_400_BAD_REQUEST)


def retrievePage(query_params):
    page = query_params.pop('page', 1)
    pagesize = query_params.pop('pageSize', 15)
    if type(page) is list:
        page = int(page[0])
    else:
        page = int(page)
    if type(pagesize) is list:
        pagesize = int(pagesize[0])
    else:
        pagesize = int(pagesize)

    return page, pagesize






