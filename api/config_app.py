# pylint: disable = R0903,E0401,C0111,C0103
"""
App level configuration
constants
"""
from rest_framework import serializers

SERIALIZE_FIELD_TYPE = {
    'DateField': serializers.DateField(format="%d/%m/%Y"),
    'DateTimeField': serializers.DateTimeField(format="%d/%m/%Y %H:%M:%S"),
    'DecimalField': serializers.FloatField()
}

QUERY_PARAMS = {
    'listview': "listview",
    'formview': "formview",
    'appmeta': "appmeta",
    'is_active': 'is_active',
    'is_deleted': 'is_deleted'
}

FORMAT_PERMISSION_CODENAME = {
    'view': 'view_{}',
    'restrict': 'restrict_{}',
    'data_restrict': 'data_restrict-{}-{}-{}'
}

PERMISSION_PREFIX = {
    'view': 'view_',
    'change': 'change_',
    'add': 'add_',
    'delete': 'delete_'
}

PERMISSION_STARTSWITH_PREFIX = {
    'restrict': 'restrict_',
    'change_restrict': 'change_restrict_',
    'change': 'change_'
}

PREDEFINED_FIELD_TYPES = {
    'DateTimeField': 'DateTimeField',
    'IntegerField': 'IntegerField',
    'DecimalField': "DecimalField",
    'DateField': 'DateField',
    'BooleanField' : 'BooleanField',
    'CharField' : 'CharField',
    'TextField' : 'TextField',
    'AutoField':'AutoField',
    'BigIntegerField' :'BigIntegerField',
    'DurationField' :'DurationField',
    'EmailField':'EmailField',
    'FloatField' :'FloatField',
    'URLField' :'URLField',
    'TimeField' : 'TimeField',
    'PositiveIntegerField': 'PositiveIntegerField',
    'PositiveSmallIntegerFiel': 'PositiveSmallIntegerFiel',
    'PositiveBigIntegerField': 'PositiveBigIntegerField',
    'BigAutoField': 'BigAutoField',

}

FOREIGN_KEY_FIELD_CONST = {
    'name': 'name'
}

INITIAL_WORKFLOW_STATUS = {
    'Draft': 'Draft',
    'Init': 'Init'
}

WORKFLOW_STATUS_TXT = 'status'

AUTHENTICATION_ERROR_MSG = {
    'Success': 'Success',
    'Failure': 'Failure',
    'Invalid Credentials': 'Invalid Credentials',
    'error': 'Provide Proper Credentials!',
    'logout': 'User Logged OUT',
    'Not Registered' : 'User Not Registered'
}

API_REQUESTS_ERROR = {
    'obj_error': 'Object Doesnt Exist',
    'permission_error': 'Access Denied',
    'json_error': 'Invalid/Empty JSON for',
    'delete_error': 'No Parameters Provided',
    'error': 'Unexpected Exception',
    'post_error': 'No Parameters Provided',
}

USER_ROLES = "guest"

default_auth_response = {
    'user' : None,
    'status' : AUTHENTICATION_ERROR_MSG["Failure"],
    'error' : AUTHENTICATION_ERROR_MSG["Invalid Credentials"],
    'is_first_login' : False,
    'last_login': None
}



COLUMN_FILTER_QUERY_ATTRIBUTE = 'filterColumn'

COLUMN_FILTER_DATA_KEY = 'columnData'

FRAMEWORK_FILE_FIELD_NAME = 'is_filefield'


class ModelDisplay:

    DISPLAY_MODELS = {

    }

    def get_display_models(self):
        return self.DISPLAY_MODELS

    def set_display_models(self, model, value):
        self.DISPLAY_MODELS[model] = value

class DisplayFields:

    DISPLAY_MODEL_FIELDS = {

    }

    def get_display_fields(self):
        return self.DISPLAY_MODEL_FIELDS

    def set_display_fields(self, model, list):
        self.DISPLAY_MODEL_FIELDS[model] = list

class WorkflowModels:

    WORKFLOW_MODEL_LIST = [

    ]

    def get_workflow_models(self):
        return self.WORKFLOW_MODEL_LIST

    def set_workflow_models(self, model):
        self.WORKFLOW_MODEL_LIST.append(model)


class MetaConfig:

    URLTOCLASS = [

    ]

    def get_url_to_class(self):
        return self.URLTOCLASS

    def set_url_to_class(self, value):
        self.URLTOCLASS.append(value)
