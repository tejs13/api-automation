# pylint: disable = E0401,C0301,C0111,R0903,R0201
""" Django Views """
import datetime
import json
import importlib

from django.apps import apps
from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.models import Group
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction, IntegrityError, models
from django.http import HttpResponse
from rest_framework import status
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from reversion import revisions as reversion
from api import ExcelExportImport
from api.bulk_approval import bulkApprovalService
from api.check_fields import check_fields, multiple_choice_field, \
    ReversionDetectChange, AllVersions
from api.config_app import PERMISSION_PREFIX, QUERY_PARAMS, INITIAL_WORKFLOW_STATUS, PERMISSION_STARTSWITH_PREFIX, \
    WORKFLOW_STATUS_TXT, AUTHENTICATION_ERROR_MSG, API_REQUESTS_ERROR, FRAMEWORK_FILE_FIELD_NAME
from api.config_metadata import FILTER_FIELD_MAPPING
from api.custom_exceptions import EmptyBodyException
from api.decorators import SpecificViewDecorator, ListViewDecorator, \
    logger_create, user_logger_create, USER_LOGS, REQ_LOGS
from api.exceptions import WorkflowExistsPatchNotAllowedException
from api.filters import genericSearch, genericfilter, retrievePage, handleCombinationData, handleSearchData, \
    handleFilterData
from api.logger_directory import excel_logs
from api.login_serializer import LoginSerializer
from api.models import MasterFiles
from api.serializers import getGenericSerializer, GenericSerializerField, \
    dropdownSerialzer
from django_filters.rest_framework import CharFilter, NumberFilter, \
    DateFromToRangeFilter, DateFilter

from api.utils import retrieve_correct_app, get_files_with_fields
from api.workflow_validators import check_edit_allow, get_pending_for_group_user
from workflow.services import approval_workflow
from commons.backends import WorkflowAuthentication
from commons.functions import get_paginated_queryset

from api.copy_data_services import CopyDataService

from api.services import DashBoardService, ExcelExportService

EXCEL_LOGS = excel_logs()
model_validators = settings.__dict__['_wrapped'].__dict__['MODEL_VALIDATORS']
FOREIGN_KEY_UI_NAME_MAP = settings.__dict__['_wrapped'].__dict__['FOREIGN_KEY_UI_NAME_MAP']
POST_SAVE_OBJ_RETURN_HOOKS = settings.__dict__['_wrapped'].__dict__['POST_SAVE_OBJ_RETURN_HOOKS']
CHECK_USER_REGISTRATION = settings.__dict__['_wrapped'].__dict__['CHECK_USER_REGISTRATION']
USER_PROFILE_MODEL_DETAILS = settings.__dict__['_wrapped'].__dict__['USER_PROFILE_MODEL_DETAILS']
USER_PROFILE_SERIALIZER = settings.__dict__['_wrapped'].__dict__['USER_PROFILE_SERIALIZER']
EXCEL_IMPORT_CONFIGS = settings.__dict__['_wrapped'].__dict__['EXCEL_IMPORT_CONFIGS']
WORKFLOW_MODEL_LIST = settings.__dict__['_wrapped'].__dict__['WORKFLOW_MODEL_LIST']
HOME_PATH = settings.__dict__['_wrapped'].__dict__['HOME_PATH']
CUSTOM_HOME_GROUP = settings.__dict__['_wrapped'].__dict__['CUSTOM_HOME_GROUP']

def reversion_post(request, serial_data, model):
    reversion.set_user(request.user)
    reversion.set_comment(request.method)
    reversion.set_date_created(date_created=datetime.datetime.now())
    if model.lower() in list(POST_SAVE_OBJ_RETURN_HOOKS.keys()):
        function_name = POST_SAVE_OBJ_RETURN_HOOKS.get(model.lower()).split('.')[-1]
        module_path, class_name = POST_SAVE_OBJ_RETURN_HOOKS.get(model.lower()).rsplit('.', 1)
        module = importlib.import_module(module_path)
        function_obj = getattr(module, function_name)
        createdObj = function_obj(serial_data)
        return createdObj

    createdObj = serial_data.save()
    return createdObj


def reversion_put(request, serial_data):
    reversion.set_user(request.user)
    reversion.set_comment(request.method)
    reversion.set_date_created(date_created=datetime.datetime.now())
    createdObj = serial_data.save()
    return createdObj

def trigger_workflow(request, request_obj, remarks, app, model, action):
    """
    Triggers workflow on passed object & save status on the requested object
    :param request: Http request object
    :param request_obj: the object on whcih workflow to be triggered
    :param remarks: remarks coming from UI
    :param app: app name <str>
    :param model: model name <str>
    :param action: action performed <Init / Approve /Reject>
    :return: None
    :rtype: None
    """
    request_status, workflow_completed = approval_workflow(app=app, model=model,
                                                           pk=request_obj.pk, action=action, remarks=remarks,
                                                           request=request, requesting_approvers=request.data.
                                                           get('approval_type'))
    request_obj.status = request_status
    request_obj.is_approved = workflow_completed
    request_obj.save()

class GenericMaster(APIView):
    """
    Generic Master for all the Specific operations
    GET     --->  /id
    POST    --->  post
    PUT     --->  /id (update)
    DELETE  --->  /id
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication, WorkflowAuthentication]
    permission_classes = [IsAuthenticated]


    @logger_create
    @SpecificViewDecorator
    def get(self, request, app, model, id):
        """
        GET for Specific
        record
        i.e GET /id
        :param request:the request object
        :param app:the app name coming from decorator
        :param model:the model name coming from decorator
        :param id:id of the model object
        :return:single object
        """
        permission = PERMISSION_PREFIX['view'] + model.lower()
        # model = apps.get_model(app, model)
        app, model = retrieve_correct_app(model)
        if request.user.groups.filter(permissions__codename=permission).exists():
            if id:
                try:
                    dataset = model.objects.filter(pk=id, is_deleted=False)
                    modelSerializer = check_fields(model)
                    if len(dataset) != 0:
                        serial = modelSerializer(dataset[0], context={"request": request, "group": None})
                        return Response(serial.data, status=status.HTTP_200_OK)
                    else:
                        raise ObjectDoesNotExist
                except ObjectDoesNotExist:
                    REQ_LOGS.error("Requested Object Doesn't Exist"
                                   + str(ObjectDoesNotExist))
                    return Response({"Error": API_REQUESTS_ERROR['obj_error']}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"Error": API_REQUESTS_ERROR['permission_error']}, status=status.HTTP_403_FORBIDDEN)

    @logger_create
    @SpecificViewDecorator
    def post(self, request, app, model):
        """
        POST the DATA
        i.e   Actual POST
        Works only for the Dedicated Model Fields
        No Relational Data POST

        :param request:the request object
        :param app:the app name coming from decorator
        :param model:the model name coming from decorator
        :return:newly created object
        """
        permission = PERMISSION_PREFIX['add'] + model.lower()
        if request.user.groups.filter(permissions__codename=permission).exists():
            # model_obj = apps.get_model(app, model)
            app, model_obj = retrieve_correct_app(model)
            # req_d = request.data
            req_d = json.loads(request.data['data'])
            file_data = []
            file_field_names = [i.name for i in list(model_obj._meta.get_fields())
                                if isinstance(i, models.BooleanField) and i.name == FRAMEWORK_FILE_FIELD_NAME]
            if file_field_names and request.FILES:
                file_data, old_files = get_files_with_fields(dict(request.FILES), file_field_names, app, model, old_files=None)
            try:
                if not req_d:
                    raise EmptyBodyException
                choice_fields = multiple_choice_field(model_obj, req_d)
                serialize = getGenericSerializer(model_obj,
                                                 model_validators[model.lower()](
                                                     req_d) if model.lower() in model_validators.keys() else None,
                                                 choice_fields
                                                 )
                req_d['status'] = INITIAL_WORKFLOW_STATUS['Draft']
                req_d['created_date'] = datetime.datetime.now()
                req_d['created_by'] = request.user.username
                req_d['last_updated_by'] = request.user.username
                req_d['last_updated_date'] = datetime.datetime.now()
                serial_data = serialize(data=req_d, context={"request": request, "group": None,
                                                             "codename": permission, "files": file_data if file_field_names and file_data else None})
                if serial_data.is_valid():
                    with transaction.atomic(), reversion.create_revision():
                        createdObj = reversion_post(request, serial_data, model)
                        REQ_LOGS.info(
                            "POST by -- {} DATA -- {} IP -- {}".format(str(request.user), str(serial_data.data),
                                                                       str(request.META.get('REMOTE_ADDR'))))
                        REQ_LOGS.info("POST Successfully Executed by -- {} -- IP -- {}".format(str(request.user), str(
                            request.META.get('REMOTE_ADDR'))))

                        # start the Approval Workflow here
                        if model.lower() in WORKFLOW_MODEL_LIST:
                            trigger_workflow(request, createdObj, 'initiated', app, model, 'Init')

                    return Response(serial_data.data, status=status.HTTP_201_CREATED)
                return Response(serial_data.errors, status=status.HTTP_400_BAD_REQUEST)
            except EmptyBodyException:
                REQ_LOGS.info(
                    " POST Error by -- {} -- IP -- {}".format(str(request.user), request.META.get('REMOTE_ADDR')))
                REQ_LOGS.error("In valid Json provided for POST by -- {}".format(str(request.user)))
                return Response({"Error": API_REQUESTS_ERROR['json_error']}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                # raise e
                REQ_LOGS.debug("In valid Json provided for POST", e)
                REQ_LOGS.info(" -- POST Error by -- {} -- IP -- {}".format(str(request.user),
                                                                           str(request.META.get('REMOTE_ADDR'))))
                REQ_LOGS.exception(e)
                return Response({"Error": API_REQUESTS_ERROR['json_error']}, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({"Error": API_REQUESTS_ERROR['permission_error']}, status=status.HTTP_403_FORBIDDEN)

    @logger_create
    @SpecificViewDecorator
    def put(self, request, app, model, id):
        """
        PUT the DATA for specific ID
        i.e    /id
        Updates the DATA for model
        Only for Dedicated fields
        NO UPDATE for Relational Fields
        :param request:the request object
        :param app:the app name coming from decorator
        :param model:the model name coming from decorator
        :param id:id of the model object
        :return:reponse the object changed
        """
        # req_d = request.data
        permission = PERMISSION_PREFIX['change'] + model.lower()
        if request.user.groups.filter(permissions__codename=permission).exists():
            # model_obj = apps.get_model(app, model)
            app, model_obj = retrieve_correct_app(model)
            req_d = json.loads(request.data['data'])
            file_data = []
            old_files = []
            is_file_field = False
            file_field_names = [i.name for i in list(model_obj._meta.get_fields())
                                if isinstance(i, models.BooleanField) and i.name == FRAMEWORK_FILE_FIELD_NAME]
            if file_field_names:
                is_file_field = True
                old_files = json.loads(request.data.get('old_files'))
                file_data, old_files = get_files_with_fields(dict(request.FILES), file_field_names, app, model, old_files=old_files)
            try:
                if not req_d:
                    raise EmptyBodyException
                obj = model_obj.objects.get(pk=id)
                if not obj:
                    raise ObjectDoesNotExist
                if not check_edit_allow(model, obj):
                    raise WorkflowExistsPatchNotAllowedException
                choice_fields = multiple_choice_field(model_obj, req_d)
                # Check if the field change permission exists
                if request.user.groups.filter(
                        permissions__codename__startswith=PERMISSION_STARTSWITH_PREFIX['change_restrict']).exists():
                    permission_list = list(request.user.groups.filter(
                        permissions__codename__startswith=PERMISSION_STARTSWITH_PREFIX['change_restrict']).values(
                        'permissions__codename'))
                    restrict_dict = {}
                    for k in permission_list:
                        if k['permissions__codename'][16:] in req_d.keys():
                            restrict_dict[k['permissions__codename'][16:]] = {'read_only': True}
                            # return Response({"Error": "Access Denied to " +k['codename'] }, status=status.HTTP_403_FORBIDDEN)
                    update_restrict_dict = {}
                    update_restrict_dict['extra_kwargs'] = restrict_dict
                    # if field change exists, serializing the obejct dynamically
                    serializer = GenericSerializerField(model_obj,
                                                        model_validators[model.lower()](
                                                            req_d) if model.lower() in model_validators.keys() else None,
                                                        choice_fields,
                                                        update_restrict_dict
                                                        )
                else:

                    serializer = GenericSerializerField(model_obj,
                                                        model_validators[model.lower()](
                                                            req_d) if model.lower() in model_validators.keys() else None,
                                                        choice_fields,
                                                        {}
                                                        )
                # role = request.user.groups.all()[0].name
                # start the approval workflow here
                # work_obj = WorkflowState(model=model, app=app, request_id=id,
                #                          role=role, state=obj.status)
                # if WORKFLOW_STATUS_TXT in req_d:
                #     req_d[WORKFLOW_STATUS_TXT] = approval_workflow(work_obj, request, req_d[WORKFLOW_STATUS_TXT])
                req_d['last_updated_by'] = request.user.username
                req_d['last_updated_date'] = datetime.datetime.now()
                serial_data = serializer(obj, data=req_d, partial=True,
                                         context={"request": request, "group": None, "model": model_obj,
                                                  "codename": permission, "files": file_data if file_field_names and file_data else None,
                                                  "old_files": old_files, "app": app, "model_name": model, "is_file_field": is_file_field})
                if serial_data.is_valid():
                    with transaction.atomic(), reversion.create_revision():
                        createdObj = reversion_put(request, serial_data)
                        REQ_LOGS.info(
                            "PUT by --> {} DATA --> {} IP -- {}".format(str(request.user), str(serial_data.data),
                                                                        str(request.META.get('REMOTE_ADDR'))))
                        REQ_LOGS.info("PUT executed Successfully by {} -- IP -- {}".format(str(request.user), str(
                            request.META.get('REMOTE_ADDR'))))
                        # trigerring workflow from beginnning if edit success
                        if model.lower() in WORKFLOW_MODEL_LIST:
                            createdObj.status = 'Initiated'
                            createdObj.save()
                            trigger_workflow(request, createdObj, 'initiated', app, model, 'Init')

                    return Response(serial_data.data, status=status.HTTP_200_OK)
                return Response(serial_data.errors, status=status.HTTP_400_BAD_REQUEST)
            except ObjectDoesNotExist as e:
                REQ_LOGS.info(
                    " Requested object doesn't exist - PUT Failed by -- {} -- IP -- {}".format(str(request.user), str(
                        request.META.get('REMOTE_ADDR'))))
                REQ_LOGS.debug(" Requested object doesn't exist by -- {} -- IP -- {}".format(str(request.user), str(
                    request.META.get('REMOTE_ADDR'))))
                REQ_LOGS.exception(e)
                return Response({"Error": API_REQUESTS_ERROR['obj_error']}, status=status.HTTP_400_BAD_REQUEST)
            except IntegrityError as e:
                REQ_LOGS.info(" PUT Failed - Integrity Error by -- {} -- IP -- {}".format(str(request.user), str(
                    request.META.get('REMOTE_ADDR'))))
                REQ_LOGS.debug(" PUT Failed - Integrity Error by -- {} -- IP -- {}".format(str(request.user), str(
                    request.META.get('REMOTE_ADDR'))))
                REQ_LOGS.exception(e)
            except EmptyBodyException as e:
                REQ_LOGS.info(
                    " Error -- PUT Failed -- empty request body by -- {} -- IP -- {}".format(str(request.user), str(
                        request.META.get('REMOTE_ADDR'))))
                REQ_LOGS.debug(
                    " Error -- PUT Failed -- empty request body by -- {} -- IP -- {}".format(str(request.user), str(
                        request.META.get('REMOTE_ADDR'))))
                REQ_LOGS.exception(e)
                return Response({"Error": API_REQUESTS_ERROR['json_error']}, status=status.HTTP_400_BAD_REQUEST)
            except WorkflowExistsPatchNotAllowedException as e:
                REQ_LOGS.info(
                    " Error -- PUT Failed -- WorkflowExistsPatchNotAllowedException -- {} -- IP -- {}".format(str(request.user), str(
                        request.META.get('REMOTE_ADDR'))))
                REQ_LOGS.debug(
                    " Error -- PUT Failed -- WorkflowExistsPatchNotAllowedException by -- {} -- IP -- {}".format(str(request.user), str(
                        request.META.get('REMOTE_ADDR'))))
                REQ_LOGS.exception(e)
                return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                # raise e
                REQ_LOGS.info(
                    "PUT Error -- by {} -- IP -- {}".format(str(request.user), str(request.META.get('REMOTE_ADDR'))))
                REQ_LOGS.debug("In valid Json provided for PUT by {} -- IP -- {}".format(str(request.user), str(
                    request.META.get('REMOTE_ADDR'))))
                REQ_LOGS.exception(e)
                return Response({"Error": str(e)}, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({"Error": API_REQUESTS_ERROR['permission_error']}, status=status.HTTP_403_FORBIDDEN)

    @logger_create
    @SpecificViewDecorator
    def delete(self, request, app, model, id):
        """
           DELETE for Specific ID
        i.e   /id
        Deletes the Whole Record
        :param request:the request object
        :param app:the app name coming from decorator
        :param model:the model name coming from decorator
        :param id:id of the model object
        :return:remaining objects of the model
        """
        permission = PERMISSION_PREFIX['delete'] + model.lower()
        if request.user.groups.filter(permissions__codename=permission).exists():
            if id:
                # model = apps.get_model(app, model)
                app, model = retrieve_correct_app(model)
                try:
                    obj = model.objects.get(pk=id)
                    if not obj:
                        raise ObjectDoesNotExist
                    with transaction.atomic(), reversion.create_revision():
                        obj = model.objects.get(pk=id)
                        obj.save()
                        reversion.set_user(request.user)
                        reversion.set_comment(request.method)
                        reversion.set_date_created(date_created=datetime.datetime.now())
                    # obj.delete()
                    obj.is_deleted = True
                    obj.save()
                    REQ_LOGS.info(
                        "Deleted object for ID -- {} -- by -- {} -- IP -- {}".format(str(id), str(request.user), str(
                            request.META.get('REMOTE_ADDR'))))
                    REQ_LOGS.info("Deleted DATA -- {}".format(str(request.user), str(obj.__dict__)))
                    return Response({"message": "Deleted Successfully"},
                                    status=status.HTTP_200_OK)
                except ObjectDoesNotExist:
                    REQ_LOGS.info(" ID doesn't exists by -- {} -- IP -- {}".format(str(request.user), str(
                        request.META.get('REMOTE_ADDR'))))
                    REQ_LOGS.debug("DELETE Object Doesnt Exist for ID -- {} by -- {} -- IP -- {}".format(str(id), str(
                        request.user), str(request.META.get('REMOTE_ADDR'))))
                    REQ_LOGS.exception(" Obejct Doesn't Exist")
                    return Response(API_REQUESTS_ERROR['obj_error'], status=status.HTTP_400_BAD_REQUEST)
                except Exception as e:
                    REQ_LOGS.info("Error -- Delete failed -- by -- {} -- IP -- {}".format(str(request.user), str(
                        request.META.get('REMOTE_ADDR'))))
                    REQ_LOGS.exception(e)
        else:
            return Response({"Error": API_REQUESTS_ERROR['permission_error']}, status=status.HTTP_403_FORBIDDEN)



def handleDropDownData(query_params, model):
    for item in query_params:
        query_params[item] = query_params[item][0]
    if model._meta.model_name.lower() in WORKFLOW_MODEL_LIST:
        add_attr = {QUERY_PARAMS['is_deleted']: False, 'is_approved': True, 'status': "Approved"}
    else:
        add_attr = {QUERY_PARAMS['is_deleted']: False}
    query_params.update(add_attr)
    objs = model.objects.filter(**query_params) \
        .order_by('name').distinct('name')
    serial = dropdownSerialzer(model)
    serializer = serial(objs, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


class ListViewDetail(APIView):
    """
    ListViewDetail for all the /LIST Operations
    GET     --->   /list
    POST    --->   /list (Conditional GET)
    DELETE  --->  /list (Conditional DELETE)
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication, WorkflowAuthentication]
    # authentication_classes = [CustomLDAPBackend]
    permission_classes = [IsAuthenticated]

    @logger_create
    @ListViewDecorator
    def get(self, request, app, model):
        """
         GET for all
        i.e   /list
        :param request:the request object
        :param app:the app name coming from decorator
        :param model:the model name coming from decorator
        :return: all the objects of the model
        """
        permission = PERMISSION_PREFIX['view'] + model.lower()
        # model_obj = apps.get_model(app, model)
        app, model_obj = retrieve_correct_app(model)
        if request.user.groups.filter(permissions__codename=permission).exists():
            page = None
            query_params = dict(request.GET)

            ###########
            # TODO custom hook project specific to allow filter only if seller uuid query param present
            if model.lower() in ['sellerproduct']:
                if 'seller_id.name' not in query_params:
                    return Response({'msg':'Error - Seller UUID Required', 'status':False}, status=status.HTTP_400_BAD_REQUEST)


            ################
            if 'page' in query_params:
                page, pagesize = retrievePage(query_params)
            if query_params and page is None and "search" not in query_params and "filter" not in query_params:
                return handleDropDownData(query_params, model_obj)
            elif 'search' in query_params and 'filter' in query_params:
                return handleCombinationData(app, model, request, page, pagesize)
            elif "search" in query_params:
                return handleSearchData(app, model, request, page, pagesize)
            elif "filter" in query_params:
                return handleFilterData(request, app, model, page, pagesize)
            else:
                if model.lower() in WORKFLOW_MODEL_LIST:
                    objs = get_pending_for_group_user(model_obj, request)
                else:
                    objs = model_obj.objects.filter(is_deleted=False).order_by('-pk')
                total_count = objs.count()
                if 'excel' in query_params:
                    pagesize = total_count
                modelSerializer = check_fields(model_obj)
                paged_queryset = get_paginated_queryset(objs, pagesize, page)
                objs = paged_queryset.object_list
                serial = modelSerializer(objs, many=True, context={"request": request, "group": None})
                if page is not None:
                    response = {
                        "total": total_count,
                        "results":  [i for i in serial.data if i is not None]
                    }
                else:
                    response = serial.data
                return Response(response, status=status.HTTP_200_OK)
        else:
            return Response({"Error": API_REQUESTS_ERROR['permission_error']}, status=status.HTTP_403_FORBIDDEN)

    @logger_create
    @ListViewDecorator
    def post(self, request, app, model):
        """
        POST for Conditional GET
        i.e    /list
        :param request:the request object
        :param app:the app name coming from decorator
        :param model:the model name coming from decorator
        :return:
        """
        if request.data:
            dict_mapp = request.data
            # model = apps.get_model(app, model)
            app, model = retrieve_correct_app(model)
            try:
                obj_filter = model.objects.filter(**dict_mapp, is_deleted=False)
                if not obj_filter:
                    raise ObjectDoesNotExist
                modelSerializer = check_fields(model)
                serial = modelSerializer(obj_filter, many=True)
                return Response(serial.data, status=status.HTTP_200_OK)
            except ObjectDoesNotExist as e:
                REQ_LOGS.debug(
                    "Objects doesn't exists for given conditions by -- {} -- IP -- {}".format(str(request.user), str(
                        request.META.get('REMOTE_ADDR'))))
                REQ_LOGS.info(" Conditional GET Failed by -- {} -- IP -- {}".format(str(request.user), str(
                    request.META.get('REMOTE_ADDR'))))
                REQ_LOGS.exception(e)
                return Response({"Error": API_REQUESTS_ERROR['obj_error']},
                                status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                REQ_LOGS.info(" Conditional GET Failed by -- {} -- IP -- {}".format(str(request.user), str(
                    request.META.get('REMOTE_ADDR'))))
                REQ_LOGS.exception(e)
                return Response({"Error": API_REQUESTS_ERROR['error']},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            REQ_LOGS.info(" Conditional GET Failed by -- {} -- IP -- {}".format(str(request.user),
                                                                                str(request.META.get('REMOTE_ADDR'))))
            REQ_LOGS.debug(
                " None Returned for GET without Conditional parameters by --> {} -- IP -- {}".format(str(request.user),
                                                                                                     str(
                                                                                                         request.META.get(
                                                                                                             'REMOTE_ADDR'))))
            return Response({"Error": API_REQUESTS_ERROR['post_error']}, status=status.HTTP_400_BAD_REQUEST)

    @logger_create
    @ListViewDecorator
    def delete(self, request, app, model):
        """
        DELETE for Contidional DELETE
        i.e    /list
        :param request:the request object
        :param app: the app name coming from decorator
        :param model:the model name coming from decorator
        :return:reponse with the remaining data
        """
        permission = PERMISSION_PREFIX['delete'] + model.lower()
        if request.user.groups.filter(permissions__codename=permission).exists():
            if request.data:
                dict_mapp = request.data
                # model = apps.get_model(app, model)
                app, model = retrieve_correct_app(model)
                # Multiple Delete for the objects i.e List of objects
                if isinstance(dict_mapp, list):
                    REQ_LOGS.info(
                        " Attempt Deleting MULTIPLE objects for ID's -- {} by -- {} -- IP -- {}".format(str(dict_mapp),
                                                                                                        str(
                                                                                                            request.user),
                                                                                                        str(
                                                                                                            request.META.get(
                                                                                                                'REMOTE_ADDR'))))
                    with transaction.atomic():
                        for i in range(dict_mapp.__len__()):
                            try:
                                objs = model.objects.filter(**dict_mapp[i], is_deleted=False)
                                if not objs:
                                    raise ObjectDoesNotExist
                                with transaction.atomic(), reversion.create_revision():
                                    objs[0].save()
                                    reversion.set_user(request.user)
                                    reversion.set_comment(request.method)
                                    reversion.set_date_created(date_created=datetime.datetime.now())
                                # objs.delete()
                                objs[0].is_deleted = True
                                objs[0].save()
                                REQ_LOGS.info(" DELETED -- {}".format(str(dict_mapp[i])))
                                REQ_LOGS.info(
                                    "DELETE by -- {} DATA -- {} -- IP -- {} ".format(str(request.user),
                                                                                     str(objs[0].__dict__), str(
                                            request.META.get('REMOTE_ADDR'))))
                            except ObjectDoesNotExist as e:
                                REQ_LOGS.info(" Further DELETE FAILED by --> {}".format(str(request.user)))
                                REQ_LOGS.debug(" Further Objects Doesnt Exist for DELETE by -- {} -- IP -- {}".format(
                                    str(request.user), str(request.META.get('REMOTE_ADDR'))))
                                REQ_LOGS.exception(e)
                                return Response({"Error": API_REQUESTS_ERROR['obj_error']},
                                                status=status.HTTP_400_BAD_REQUEST)
                            except (IntegrityError, APIException) as e:
                                REQ_LOGS.debug(
                                    "Data INtegrity Exception occured by -- {} -- IP -- {}".format(str(request.user),
                                                                                                   str(request.META.get(
                                                                                                       'REMOTE_ADDR'))))
                                REQ_LOGS.info("Delete failed by {} -- IP -- {}".format(str(request.user), str(
                                    request.META.get('REMOTE_ADDR'))))
                                REQ_LOGS.exception(e)
                                return Response({"Error": API_REQUESTS_ERROR['error']},
                                                status=status.HTTP_400_BAD_REQUEST)
                else:
                    # delete for Matching Conditions for the objects
                    try:
                        objs = model.objects.filter(**dict_mapp, is_deleted=False)
                        REQ_LOGS.info(
                            "Attempt Deleting CONDITIONAL objects for Conditon  -- {} by -- {} -- IP --{}".format(
                                str(dict_mapp), str(request.user), str(request.META.get('REMOTE_ADDR'))))
                        if not objs:
                            raise ObjectDoesNotExist
                        with transaction.atomic(), reversion.create_revision():
                            # [objs[i].save() for i in range(len(objs))]
                            for i in range(len(objs)):
                                objs[i].is_deleted = True
                                objs[i].save()
                                REQ_LOGS.info(
                                    "DELETE by -- {} DATA -- {} -- IP -- {}".format(str(request.user),
                                                                                    str(objs[i].__dict__), str(
                                            request.META.get('REMOTE_ADDR'))))
                            reversion.set_user(request.user)
                            reversion.set_comment(request.method)
                            reversion.set_date_created(date_created=datetime.datetime.now())
                            # objs.delete()
                            REQ_LOGS.info(
                                " DELETED objects Successfully for Matching Conditions -- {} -- by -- {} -- IP -- {} ".format(
                                    str(dict_mapp), str(request.user), str(request.META.get('REMOTE_ADDR'))))
                    except ObjectDoesNotExist as e:
                        REQ_LOGS.info(" DELETE FAILED ")
                        REQ_LOGS.debug(
                            " Objects Doesn't Exists for given matching conditions by -- {} -- IP -- {}".format(
                                str(request.user), str(request.META.get('REMOTE_ADDR'))))
                        REQ_LOGS.exception(e)
                        return Response({"Error": API_REQUESTS_ERROR['obj_error']},
                                        status=status.HTTP_400_BAD_REQUEST)
                    except (IntegrityError, APIException) as e:
                        REQ_LOGS.warning(" Data Integrity not maintained", e)
                        REQ_LOGS.debug(" Delete failed APIException")
                        REQ_LOGS.info(" Delete Failed by -- {} -- IP -- {}".format(str(request.user), str(
                            request.META.get('REMOTE_ADDR'))))
                        REQ_LOGS.exception(e)
                        return Response({"Error": API_REQUESTS_ERROR['error']},
                                        status=status.HTTP_400_BAD_REQUEST)

                return Response({'Received Conditional data': request.data}, status=status.HTTP_200_OK)
            else:
                REQ_LOGS.info(
                    " Delete Failed -- No Conditional Parameters by -- {} -- IP -- {}".format(str(request.user), str(
                        request.META.get('REMOTE_ADDR'))))
                REQ_LOGS.debug(" None Deleted without deletion parameters by -- {} -- {}  ".format(str(request.user),
                                                                                                   str(request.META.get(
                                                                                                       'REMOTE_ADDR'))))
                return Response({"Error": API_REQUESTS_ERROR['delete_error']}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"Error": API_REQUESTS_ERROR['permission_error']}, status=status.HTTP_403_FORBIDDEN)

class CsrfExemptSessionAuthentication(SessionAuthentication):

    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening

class LoginView(APIView):

    authentication_classes = [CsrfExemptSessionAuthentication]

    @user_logger_create
    def post(self, request):
        """
        Login view for user Login and Authentication
        provided the username and Password in Json via POST
        and Token Generation
        :param request: the request object
        :return:Token for success else error with message
        """

        serializer = LoginSerializer(data=request.data)
        grp, created = Group.objects.get_or_create(name="default")
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            status = serializer.validated_data["status"]
            error = serializer.validated_data["error"]
            # type = serializer.validated_data["type"]
            if user:
                login(request, user)
                token, created = Token.objects.get_or_create(user=user)
                grp = Group.objects.get(name="default")
                grp.user_set.add(user)
                path = ''
                if user.groups.filter(name=CUSTOM_HOME_GROUP).exists():
                    path = HOME_PATH
                # add_user(user, type)
                REQ_LOGS.info("Token Successful for user -- {} -- IP -- {}".format(str(user), str(
                    request.META.get('REMOTE_ADDR'))))
                USER_LOGS.info("Token Successful for user -- {} -- IP -- {}".format(str(user), str(
                    request.META.get('REMOTE_ADDR'))))
                if CHECK_USER_REGISTRATION:
                    serializer_name = USER_PROFILE_SERIALIZER.split('.')[-1]
                    module_path, class_name = USER_PROFILE_SERIALIZER.rsplit('.', 1)
                    module = importlib.import_module(module_path)
                    serializer_class = getattr(module, serializer_name)
                    user_profile_model = apps.get_model(USER_PROFILE_MODEL_DETAILS['app'],
                                                        USER_PROFILE_MODEL_DETAILS['model'])
                    kwargs = {
                        f'{USER_PROFILE_MODEL_DETAILS["search_on_field"]}': user.username
                    }
                    user_profile_obj = user_profile_model.objects.get(**kwargs)
                    serial = serializer_class(user_profile_obj)
                    return Response({"User Data": serial.data, "Your Token": token.key, "status": status,"path":path}, status=200)
                return Response({"Your Token": token.key, "status": status,"path":path}, status=200)
            elif error == AUTHENTICATION_ERROR_MSG["Invalid Credentials"]:
                return Response({"message": error, "status": status}, status=400)
            elif error == AUTHENTICATION_ERROR_MSG['Not Registered']:
                return Response({"Error" : AUTHENTICATION_ERROR_MSG['Not Registered']}, status=400)
            else:
                return Response({"Error": AUTHENTICATION_ERROR_MSG['error']}, status=400)
        else:
            return Response(AUTHENTICATION_ERROR_MSG['error'],status=400)


class LogoutView(APIView):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Logout And Session Destroy
        :param request:the request object
        :return: user log out
        """
        logout(request)
        USER_LOGS.info("user --> {} Logged Out Successfully ".format(str(request.user)))
        return Response(AUTHENTICATION_ERROR_MSG['logout'], status=status.HTTP_200_OK)


class ReversionView(APIView):
    @logger_create
    @SpecificViewDecorator
    def get(self, request, app, model, id):
        """
        To get All the
        Versions History of the Object
        :param request:the request object
        :param app: the app name coming from decorator
        :param model: the model name coming from decorator
        :param id: the id of model for which the versions to be fetched
        :return:  returns the response for all the versions of the particular model
        """
        # model = apps.get_model(app, model)
        app, model = retrieve_correct_app(model)
        try:
            objs = model.objects.get(pk=id)
            changes = ReversionDetectChange(objs)
            return Response(changes)
        except ObjectDoesNotExist as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class ModelVersions(APIView):
    @logger_create
    @SpecificViewDecorator
    def get(self, request, app, model):
        """
        To get All the
        Versions for particular
        Model
        :param request: the request object
        :param app: the app name coming from decorator
        :param model: the model name coming from decorator
        :return: returns the response for all the versions of the particular model
        """
        model = apps.get_model(app, model)
        ver_list = AllVersions(model)
        return Response(ver_list)


class ExcelExport(APIView):
    # parser_classes = [MultiPartParser, FormParser]
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    @SpecificViewDecorator
    def post(self, request, app, model):
        data = request.data
        # model_obj = apps.get_model(app, model)
        app, model_obj = retrieve_correct_app(model)
        # if not request.data.get('primary_key'):
        #     raise Exception("Primary Key Not Received from UI")
        pks = [i[model_obj._meta.pk.attname] for i in request.data.get('results')] \
            if not request.data.get("results") == "all" else 'all'
        export_service = ExcelExportService()
        return export_service.export(pks, request, app, model)

class ExcelImport(APIView):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @SpecificViewDecorator
    def post(self, request, app, model):
        try:
            if not model.lower() in EXCEL_IMPORT_CONFIGS.keys():
                return Response('Error : Model Not Registered for Excel Import', status=status.HTTP_404_NOT_FOUND)
            # model_obj = apps.get_model(app, model)
            app, model_obj = retrieve_correct_app(model)
            files = request.FILES
            excel_file = files.get('file').file
            ex = ExcelExportImport.ExcelImportExport(EXCEL_LOGS)
            result = ex.import_excel(excel_file, EXCEL_IMPORT_CONFIGS[model.lower()], model_obj, request, app, model)
            if type(result) == list:
                return Response('Excel Imported, Inserted Data: %s, Updated Data: %s, Failed Data: %s, Message: %s'
                                % (len(result[0]), len(result[1]), len(result[2]), result[3]),
                                status=status.HTTP_200_OK)
            else:
                return Response(str(result), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            EXCEL_LOGS.exception(e)
            return Response('Error Occurred -> %s' % str(e), status=status.HTTP_200_OK)


class ListFilter(APIView):
    @ListViewDecorator
    def get(self, request, app, model):
        try:
            if request.GET.__len__() > 0:
                # model_obj = apps.get_model(app, model)
                app, model_obj = retrieve_correct_app(model)
                query_dict = request.GET.dict()
                filter_dict={}
                for i in list(query_dict.keys()):
                    if '.name' in i:
                        if FOREIGN_KEY_UI_NAME_MAP[model.lower()]['type']=='integer':
                            filter_dict[FOREIGN_KEY_UI_NAME_MAP[model.lower()]['field']] = NumberFilter(lookup_expr='iexact')
                            old_value = query_dict[i]
                            del query_dict[i]
                            i = FOREIGN_KEY_UI_NAME_MAP[model.lower()]['field']
                            query_dict[i] = old_value
                        if FOREIGN_KEY_UI_NAME_MAP[model.lower()]['type'] == 'text':
                            filter_dict[FOREIGN_KEY_UI_NAME_MAP[model.lower()]['field']] = CharFilter(lookup_expr='iexact')
                            old_value = query_dict[i]
                            del query_dict[i]
                            i = FOREIGN_KEY_UI_NAME_MAP[model.lower()]['field']
                            query_dict[i] = old_value
                    if '_' in query_dict[i]:
                        values = query_dict[i].split('_')
                        op = values[0]
                        value = "_".join(values[1:])
                        query_dict[i] = value
                        if op in FILTER_FIELD_MAPPING['integer']:
                            filter_dict[i] = NumberFilter(field_name=i,lookup_expr=op)
                        elif op in FILTER_FIELD_MAPPING['text']:
                            filter_dict[i] = CharFilter(field_name=i, lookup_expr=op)
                model_filter = genericfilter(model_obj, filter_dict)
                f = model_filter(query_dict, queryset=model_obj.objects.all())
                modelSerializer = check_fields(model_obj)
                serial = modelSerializer(f.qs, many=True, context={"request": request, "group": None})
                return Response(serial.data, status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            REQ_LOGS.exception(e)
            return Response(status=status.HTTP_400_BAD_REQUEST)


class SearchFilter(APIView):
    @ListViewDecorator
    def get(self, request, app, model):
        try:
            DynamicSearchFilter = genericSearch(model)
            # model_obj = apps.get_model(app, model)
            app, model_obj = retrieve_correct_app(model)
            model_filter = DynamicSearchFilter()
            objs = model_obj.objects.filter(is_deleted=False).order_by('-pk')
            final_qs = model_filter.filter_queryset(request, objs, APIView)
            modelSerializer = check_fields(model_obj)
            serial = modelSerializer(final_qs, many=True, context={"request": request, "group": None})
            return Response(serial.data, status=status.HTTP_200_OK)
        except Exception as e:
            REQ_LOGS.exception(e)
            return Response(status=status.HTTP_400_BAD_REQUEST)


class DownloadMasterFiles(APIView):

    def get(self, request, *args, **kwargs):
        try:
            uid = kwargs.get('uid')
            master_file_obj = MasterFiles.objects.get(pk=uid)
            file_path = master_file_obj.file.path
            file_name = file_path.split('\\')[-1]
            REQ_LOGS.info(f'Request to download file -- {file_name} -- from -- {request.user.username} '
                          f'-- by -- {request.META.get("REMOTE_ADDR")}')
            file = open(file_path, 'rb')
            response = HttpResponse(file, content_type='application/force-download', )
            response['Content-Disposition'] = 'attachment; filename=' + file_name
            REQ_LOGS.info(f'File Download Successful file -- {file_name} -- from -- {request.user.username} '
                          f'-- by -- {request.META.get("REMOTE_ADDR")}')
            return response
        except Exception as e:
            REQ_LOGS.exception(e)
            return Response('Exception Occurred while downloading', status=status.HTTP_400_BAD_REQUEST)


class CopyDataView(APIView):

    def post(self, request, app, model):
        """
        Purpose:For copy data
        """
        try:
            service_object = CopyDataService()
            response = service_object.copy_data(request, app, model)
            return response
        except Exception as e:
            REQ_LOGS.debug('Exception Occurred while POST copy Data')
            REQ_LOGS.exception(e)
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


    def get(self, request, app, model):
        """
        To get data for copy data
        """
        try:
            service_object = CopyDataService()
            response = service_object.get_data_for_copy(request, app, model)
            return response
        except Exception as e:
            REQ_LOGS.debug('Exception Occurred while GET copy Data')
            REQ_LOGS.exception(e)
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)



class BulkApprovalViewView(APIView):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, app, model):
        """
        Purpose:For copy data
        """
        try:
            reject = True if request.GET else False
            bulk_service = bulkApprovalService()
            response = bulk_service.bulk_approve(request, app, model, reject)
            return response
        except Exception as e:
            REQ_LOGS.debug('Exception Occurred while POST copy Data')
            REQ_LOGS.exception(e)
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)




class DashboardView(APIView):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Purpose:For dynamic dashboard data
        """
        try:
            dash_service = DashBoardService()
            response = dash_service.get_models_summary(request.data)
            return response
        except Exception as e:
            REQ_LOGS.debug('Exception Occurred while Dashboard POST')
            REQ_LOGS.exception(e)
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
