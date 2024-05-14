# pylint: disable = R0903,E0401,C0111,C0103
"""
Module to check the and
bifurcate the foreign key
and related fields for serilization
"""
from deepdiff import DeepDiff
from django.conf import settings
from django.db import models
from multiselectfield import MultiSelectField
from rest_framework import serializers, fields
from reversion.models import Version, Revision

from api.config_app import PREDEFINED_FIELD_TYPES, SERIALIZE_FIELD_TYPE, FRAMEWORK_FILE_FIELD_NAME
from api.serializers import GenericTrackSerializer, \
    ReverseStringSerializer, ReverseNestedSerializer
from django.contrib.auth.models import User
# from api.models import CustomUser

model_field_choices = settings.__dict__['_wrapped'].__dict__['MODEL_FIELD_CHOICES']
MASTERS_APP_NAME = settings.__dict__['_wrapped'].__dict__['MASTERS_APP_NAME']
DATE_INPUT_FORMAT = settings.__dict__['_wrapped'].__dict__['DATE_INPUT_FORMAT']
DATE_TIME_INPUT_FORMAT = settings.__dict__['_wrapped'].__dict__['DATE_TIME_INPUT_FORMAT']
TIME_INPUT_FORMAT = settings.__dict__['_wrapped'].__dict__['TIME_INPUT_FORMAT']

def serial_field_format(model):
    """
    to bifurcate fields format
    for serializaion
    :param model: reference model for fields
    :return: formatted fields for the model
    """
    format_fields = {i.name: SERIALIZE_FIELD_TYPE[i.get_internal_type()] for i in list(
        filter(lambda x: (x.get_internal_type() in SERIALIZE_FIELD_TYPE.keys()), list(model._meta.get_fields())))}
    return format_fields


def check_fields(model):
    """
    Common funtion to bifurcate
    the fields of the model
    i.e Foreignkey field, related field, etc.
    :param model: the model
    :return:the dict for generic nested serialization logic
    """
    foreign_keys = {}
    related_fields = {}
    simple_fields = []
    # format_fields = serial_field_format(model)
    for field in model._meta.get_fields():
        if field.get_internal_type() == PREDEFINED_FIELD_TYPES["DateField"]:
            foreign_keys[field.name] = serializers.DateField(format="%d/%m/%Y")
        if field.get_internal_type() == PREDEFINED_FIELD_TYPES["DateTimeField"]:
            foreign_keys[field.name] = serializers.DateTimeField(format="%d/%m/%Y %H:%M:%S")
        if field.get_internal_type() == PREDEFINED_FIELD_TYPES["DecimalField"]:
            foreign_keys[field.name] = serializers.FloatField()
        # if isinstance(field,models.ForeignKey):
        #     foreign_keys[field.name + " value"]  = serializers.StringRelatedField(source=field.name,read_only=True)
        #     print("in is instance")
        #     continue
        if isinstance(field, models.BooleanField) and field.name == FRAMEWORK_FILE_FIELD_NAME:
            foreign_keys['files'] = serializers.SerializerMethodField()

        if isinstance(field, models.ForeignKey):
            test = {}
            for rel_field in field.related_model._meta.get_fields():
                if rel_field.get_internal_type() == PREDEFINED_FIELD_TYPES["DateTimeField"]:
                    test[rel_field.name] = serializers.DateTimeField(format="%d/%m/%Y %H:%M:%S")
            serial = ReverseNestedSerializer(field.related_model, test)
            foreign_keys[field.name] = serial(read_only=True)
            continue
        elif field.is_relation:
            related_model = field.related_model
            if MASTERS_APP_NAME == related_model._meta.app_label:
                serial = GenericTrackSerializer(field.related_model)
                related_fields[field.name] = serial(many=True)
                continue
            else:
                continue
        else:
            simple_fields.append(field.name)
            continue

    combine = {**foreign_keys, **related_fields, }
    serializer_uniq = ReverseStringSerializer(model, combine)
    # serializer = serializer_uniq(objs, many=True)
    return serializer_uniq


def multiple_choice_field(model, req_data):
    """
    Serialze the multiple choice
    field separately
    :param model:the model
    :return:dict with multiselectfields if exists for serialization
    """
    # pass
    choice_fields = {}
    for field in model._meta.get_fields():
        if isinstance(field, MultiSelectField):
            choice_fields[field.name] = fields.MultipleChoiceField(choices=model_field_choices[
                model._meta.model_name] if model._meta.model_name in model_field_choices.keys() else None)

        if field.get_internal_type() == PREDEFINED_FIELD_TYPES["DateField"]:
            if req_data.get(field.name):
                choice_fields[field.name] = serializers.DateField(input_formats=DATE_INPUT_FORMAT)
            elif field.name not in req_data:
                choice_fields[field.name] = serializers.DateField(required=False)
            elif field.null:
                choice_fields[field.name] = serializers.DateField(allow_null=True)
        if field.get_internal_type() == PREDEFINED_FIELD_TYPES["DateTimeField"]:
            if req_data.get(field.name):
                choice_fields[field.name] = serializers.DateTimeField(input_formats=DATE_TIME_INPUT_FORMAT)
            elif field.name not in req_data:
                choice_fields[field.name] = serializers.DateTimeField(required=False)
            elif field.null:
                choice_fields[field.name] = serializers.DateTimeField(allow_null=True)
        if field.get_internal_type() == PREDEFINED_FIELD_TYPES["TimeField"]:
            if req_data.get(field.name):
                choice_fields[field.name] = serializers.TimeField(input_formats=TIME_INPUT_FORMAT)
            elif field.name not in req_data:
                choice_fields[field.name] = serializers.TimeField(required=False)
            elif field.null:
                choice_fields[field.name] = serializers.TimeField(allow_null=True)

    return choice_fields


def DateWrap(versions, n, i):
    """
    Wraps the Date for every
    instance of Diff change
    :param versions: the current version for the object
    :param n: variable
    :param i: variable
    :return:
    """
    rev_id = versions.revision_id
    rev_obj = Revision.objects.get(id=rev_id)
    user_id = rev_obj.user_id
    user = User.objects.get(pk=user_id)
    date = rev_obj.date_created

    diff = DeepDiff(n, i,
                    exclude_paths=["root['created_date']", "root['last_updated_date']", "root['last_updated_by']"],
                    ignore_type_in_groups=[(int, float, None, type, str, User)])

    # class WrapReversion(DeepDiff):
    #     def __init__(self):
    #         DeepDiff.__init__(self, n, i, exclude_paths=["root['created_date']", "root['last_updated_date']",
    #                                                      "root['last_updated_by']"])
    #         # DeepDiff.__init__(self, n, i,)
    #         self.date = date
    #         self.user = user.username
    #
    # return WrapReversion()
    return diff, date, user.username


def ReversionDetectChange(obj):
    """
    List all the versions for the
    passed Object along with the
    created data.
    :param obj:the obejct for which the versions to be fetched
    :return:the deepdif dicationary describing the changes
    """
    versions = Version.objects.get_for_object(obj)
    created_rev_id = versions[(len(versions) - 1)].revision_id
    created_rev_obj = Revision.objects.get(id=created_rev_id)
    created_user_id = created_rev_obj.user_id
    user = User.objects.get(pk=created_user_id)
    created_date = created_rev_obj.date_created
    created = []
    info = {}
    info['data'] = versions[(len(versions) - 1)].field_dict
    info['created_at'] = created_date
    info['created_by'] = user.username
    created.append(info)
    diffs = []
    versions_list = []
    for i in range(len(versions)):
        versions_list.append(versions[i].field_dict)
    versions_list.reverse()
    j = len(versions)
    for n, i in zip(versions_list, versions_list[1:]):
        # callable = DateWrap(versions[j - 2], n, i)
        # diff_wrapper = callable
        diff = DateWrap(versions[j - 2], n, i)
        info = {}
        if diff[0]:
            info['change'] = diff[0]
            # if diff_wrapper:
            info['date'] = diff[1]
            info['user'] = diff[2]
            diffs.append(info)
        j = j - 1
    return created, diffs[::-1]


def AllVersions(model):
    """
    describes all the verisons
    for the particular model
    :param model: the model
    :return: the verrsion for specific model
    """
    versions = Version.objects.get_for_model(model)
    versions_list = []
    for i in range(len(versions)):
        versions_list.append(versions[i].field_dict)
    return versions_list[::-1]


def interrupt():
    pass
    # print("Terminating the script !!!!")
    # sys.exit()
