# pylint: disable = E0401,R0903,E0401,C0111,C0103


"""
module to generate
the metadata for the
apss and model
"""
import sys
from datetime import datetime

from django.apps import apps
from django.conf import settings
from django.db import models
from django.db.models import Q
from rest_framework.metadata import SimpleMetadata
from api.config_app import FORMAT_PERMISSION_CODENAME, QUERY_PARAMS, PERMISSION_STARTSWITH_PREFIX, \
    PREDEFINED_FIELD_TYPES, FOREIGN_KEY_FIELD_CONST, COLUMN_FILTER_QUERY_ATTRIBUTE, COLUMN_FILTER_DATA_KEY
from api.config_metadata import LISTVIEW_CONST, EXTRA_META_CONST \
    , APPMETA_CONST, CONST_PRIMARY_KEY, CONST_FOREIGN_KEY, FILTER_LIST_CONST
from api.config_restrict_fields import RESTRICT
from api.models import BaseModel
from api.utils import import_string, retrieve_correct_app
from workflow.services import to_show_approval_button

DISPLAY_MODELS = settings.__dict__['_wrapped'].__dict__['DISPLAY_MODELS']
WORKFLOW_MODEL_LIST = settings.__dict__['_wrapped'].__dict__['WORKFLOW_MODEL_LIST']
# DISPLAY_MODEL_FIELDS = settings.__dict__['_wrapped'].__dict__['DISPLAY_MODEL_FIELDS']
EXTRA_USER_META = settings.__dict__['_wrapped'].__dict__['EXTRA_USER_META']
SECTION_ICONS = settings.__dict__['_wrapped'].__dict__['SECTION_ICONS']
URL_METADATA_CLASS = settings.__dict__['_wrapped'].__dict__['URL_METADATA_CLASS']
AUTO_GENERATION_SECTIONS = settings.__dict__['_wrapped'].__dict__['AUTO_GENERATION_SECTIONS']
FOREIGN_KEY_UI_NAME_MAP = settings.__dict__['_wrapped'].__dict__['FOREIGN_KEY_UI_NAME_MAP']


def prepare_referenced_fk_fields_filter(model):
    for field in list(model._meta.get_fields()):
        if isinstance(field, models.ForeignKey):
            if model._meta.model_name in FOREIGN_KEY_UI_NAME_MAP:
                if field.name in FOREIGN_KEY_UI_NAME_MAP[model._meta.model_name]:
                    reference_fields = FOREIGN_KEY_UI_NAME_MAP[model._meta.model_name][field.name]
                    for ref_field in reference_fields:
                        info = {}
                        info['field'] = str(field.name) + '.' + ref_field['field'].split("__")[-1]
                        info['headerName'] = ref_field['field'].split("__")[-1].capitalize()
                        info['type'] = ref_field['type']
                        model.UI_Meta.ui_specs[QUERY_PARAMS['listview']].append(info)
                else:
                    pass

            else:
                pass


def determine_listview_metadata(request, model):
    """
    generates the metadata for columns 
    in the frontend grid
    :param request: the request object
    :param model: the model for which the columns to be fetched
    :return: the metadata dict with different sections
    """
    DISPLAY_MODEL_FIELDS = {}
    model.UI_Meta.ui_specs[QUERY_PARAMS['listview']] = []
    field_list = []

    if COLUMN_FILTER_QUERY_ATTRIBUTE in request.GET:
        DISPLAY_MODEL_FIELDS[model._meta.model_name] = request.data.get(COLUMN_FILTER_DATA_KEY)
    else:
        DISPLAY_MODEL_FIELDS = settings.__dict__['_wrapped'].__dict__['DISPLAY_MODEL_FIELDS']

    for field in model._meta.get_fields():
        if request.user.groups.filter(
                permissions__codename=FORMAT_PERMISSION_CODENAME['restrict']
                        .format(field.name)).exists():
            field_list.append(field.name)

    base_fields = [i for i in list(BaseModel._meta.get_fields()) if
                   i.name in DISPLAY_MODEL_FIELDS[model._meta.model_name]]

    ordered_fields = []
    for i in list(model._meta.get_fields()):
        if i.name in [j.name for j in list(BaseModel._meta.get_fields())]:
            continue
        if i.name in DISPLAY_MODEL_FIELDS[model._meta.model_name] and i.name not in base_fields:
            ordered_fields.append(i)
    unique_together_fields = [element for tupl in model._meta.unique_together for element in tupl]
    for field in ordered_fields + base_fields:
        if field.name in field_list:
            continue
        info = {}
        if field.name in RESTRICT:
            info['field'] = None
            continue
        info['field'] = field.name
        info['headerName'] = field.name.replace("_", " ").capitalize()
        if field.is_relation and not isinstance(field, models.ForeignKey):
            continue
        elif isinstance(field, models.ForeignKey):
            info['field'] = str(field.name) + '.' + FOREIGN_KEY_FIELD_CONST['name']
            info['type'] = CONST_FOREIGN_KEY
        if field.primary_key:
            # continue
            info['headerCheckboxSelection'] = True
            info['checkboxSelection'] = field.editable
            info['primarykeyfield'] = str(field.name)
            info['type'] = CONST_PRIMARY_KEY
        if field.get_internal_type() in PREDEFINED_FIELD_TYPES.keys():
            info['filter'] = LISTVIEW_CONST[field.get_internal_type()]
            info['type'] = FILTER_LIST_CONST[field.get_internal_type()]
        if field.name in unique_together_fields:
            info['unique_together'] = True
        model.UI_Meta.ui_specs[QUERY_PARAMS['listview']].append(info)
    prepare_referenced_fk_fields_filter(model)
    return model.UI_Meta.ui_specs[QUERY_PARAMS['listview']]


def determine_appmeta_metadata(request, app):
    all_groups = request.user.groups.all().prefetch_related('permissions')
    check = lambda x :request.user.groups.filter(
        permissions__codename=FORMAT_PERMISSION_CODENAME['view'].format(x.replace(' ','_').lower())).exists()
    meta2 = {k:v for k,v in EXTRA_USER_META.items() if check(k)}
    auto = {}
    final_meta = []
    for screen in meta2.keys():
        if screen in AUTO_GENERATION_SECTIONS:
            under_meta = {}
            under_meta['sectionName'] = screen
            under_meta['icon'] = SECTION_ICONS[screen]
            under_meta['screens'] = generate_master_screens(request, meta2[screen][0]['app'], all_groups)
            final_meta.append(under_meta)
        else:
            final_meta.append(generate_extra_screens(request, screen, EXTRA_USER_META[screen], all_groups))
    # auto["auto_generation_sections"] = [screen for screen in AUTO_GENERATION_SECTIONS if check(screen)]
    # final_meta.append(auto)
    return final_meta


def generate_master_screens(request, app, all_groups):
    in_models = list(apps.get_app_config(app).get_models())
    permit_models = list(filter(lambda x :request.user.groups.filter(permissions__codename=FORMAT_PERMISSION_CODENAME['view']
                                                                     .format(x._meta.model_name)).exists(), in_models))
    permit_models = sorted(set(permit_models), key=lambda x: x._meta.model_name, reverse=False)
    screens = []
    for model in permit_models:
        screens.append(retrieve_all_permissions_meta(request, model, all_groups, 'master'))
    return screens

def retrieve_all_permissions_meta(request, model_obj, all_groups, m_type):
    info={}
    m_all=[]
    for group in all_groups:
        all_permi = list(group.permissions.filter(
            content_type__app_label=model_obj._meta.app_label,
            content_type__model=model_obj._meta.model_name).values('codename'))
        m_all = m_all + all_permi
    info['screen'] = str(model_obj._meta.model_name).capitalize()
    info['title'] = DISPLAY_MODELS[model_obj._meta.model_name] if model_obj._meta.model_name in DISPLAY_MODELS.keys() else model_obj._meta.model_name
    info['type'] = m_type
    info['model'] = model_obj._meta.model_name
    info['related_app'] = model_obj._meta.app_label
    info['permissions'] = m_all
    return info

def generate_extra_screens(request, screen, extra_meta, all_groups):
    extra_meta_defined = {
        'sectionName': screen,
        'icon': SECTION_ICONS[screen],
        'screens': []#EXTRA_USER_META[screens]
    }
    for scr in extra_meta:
        if scr['type'] == 'subsection':
            if request.user.groups.filter(permissions__codename=FORMAT_PERMISSION_CODENAME['view']
                    .format(scr['screen'].lower())).exists():
                m_all = []
                for group in all_groups:
                    all_permi = list(group.permissions.filter(
                        content_type__app_label=scr['screen']).values('codename'))
                    m_all = m_all + all_permi
                scr['permissions'] = m_all
                extra_meta_defined['screens'].append(scr)
        elif scr['type'] == 'model':
            model_obj = apps.get_model(scr['app'],scr['model'])
            if request.user.groups.filter(permissions__codename=FORMAT_PERMISSION_CODENAME['view']
                    .format(model_obj._meta.model_name)).exists():
                u_meta = retrieve_all_permissions_meta(request, model_obj, all_groups, m_type='model')
                extra_meta_defined['screens'].append(u_meta)

    return extra_meta_defined



def determine_formview_metadata(request, model):
    """
    returns the static hard-coded metadata
    of the models to generate forms
    :param request: the request object
    :param model: the model for which the metadata to be returned
    :return: the metadata for formview
    """
    field_list = []
    grps = request.user.groups.all().prefetch_related('permissions')
    for group in grps:
        permission = list(group.permissions.filter(
            (Q(content_type__app_label=model._meta.app_label) & Q(content_type__model=model._meta.model_name)) &
            (Q(codename__startswith=PERMISSION_STARTSWITH_PREFIX['change_restrict']) | Q(
                codename__startswith=PERMISSION_STARTSWITH_PREFIX['restrict'])
             | Q(codename__startswith=PERMISSION_STARTSWITH_PREFIX['change']))).values('codename'))
        if len(permission) > 0:
            field_list = field_list + permission
        else:
            continue
    permit = {'permissions': field_list}
    model.UI_Meta.ui_specs["formview"][0].update(permit)
    # if request.parser_context['kwargs']['model'] in WORKFLOW_MODEL_LIST:
    #     temp = {'show_section': to_show_approve_button(request)}
    #     model.UI_Meta.ui_specs["formview"][0].update(temp)

    if request.parser_context['kwargs']['model'].lower() in WORKFLOW_MODEL_LIST:
        if 'id' in request.query_params and str(request.query_params.get('id')) != 'new':
            import copy
            temp_formview = copy.deepcopy(model.UI_Meta.ui_specs["formview"])
            temp = {'show_section': to_show_approval_button(request, request.query_params.get('id'), model),
                    'show_card': True}
            temp_formview[0].update(temp)
            return temp_formview
    return model.UI_Meta.ui_specs["formview"]


class ApiMetadata():
    """
    Options call class
    """

    @staticmethod
    def determine_metadata(request):
        """
        Main metadata method for
        the options call
        :param request:
        :return:
        """
        if request.query_params.get('set') == QUERY_PARAMS['listview']:
            # model = apps.get_model(request.parser_context['kwargs']['app'],
            #                        request.parser_context['kwargs']['model'])
            app, model = retrieve_correct_app(request.parser_context['kwargs']['model'])
            return determine_listview_metadata(request, model)

        elif request.query_params.get('set') == QUERY_PARAMS['appmeta']:
            app = request.parser_context['kwargs']['app']
            return determine_appmeta_metadata(request, app)

        elif request.query_params.get('set') == QUERY_PARAMS['formview']:
            # model = apps.get_model(request.parser_context['kwargs']['app'],
            #                        request.parser_context['kwargs']['model'])
            app, model = retrieve_correct_app(request.parser_context['kwargs']['model'])
            return determine_formview_metadata(request, model)



class MinimalMetadata(SimpleMetadata):
    """
    Custom metadata for the model
    i.e Listview & appmeta
    """

    def determine_metadata(self, request, view):
        urlName = request.resolver_match.url_name
        meta_class_name = import_string(URL_METADATA_CLASS[urlName])
        meta_function = getattr(getattr(sys.modules[__name__], meta_class_name), 'determine_metadata')
        return meta_function(request)

