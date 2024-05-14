# pylint: disable = R0903,E0401,C0111,C0103
"""
Serilizers for Data Conversion
JSON  <--->  Django Objects
"""

from django.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from api.config_app import FORMAT_PERMISSION_CODENAME
from api.config_restrict_fields import restrict_fields
from api.models import MasterFiles
from commons.dms import MossDms

MASTER_FILES_MOSS_UPLOAD = settings.__dict__['_wrapped'].__dict__['MASTER_FILES_MOSS_UPLOAD']
MOSS_BASE_URL = settings.__dict__['_wrapped'].__dict__['MOSS_BASE_URL']
MOSS_USERNAME = settings.__dict__['_wrapped'].__dict__['MOSS_USERNAME']
MOSS_PASSWORD = settings.__dict__['_wrapped'].__dict__['MOSS_PASSWORD']
RELATIVE_FOLDER_TO_UPLOAD_URL = settings.__dict__['_wrapped'].__dict__['RELATIVE_FOLDER_TO_UPLOAD_URL']
DATA_RESTRICT_PERMISSIONS = settings.__dict__['_wrapped'].__dict__['DATA_RESTRICT_PERMISSIONS']


def getGenericSerializer(model_arg, model_validations, choice_fields):
    """
    Simple generic serializer to serialize all
    the fields of the Model without relation
    :param model_arg:model for serializer
    :param model_validations:model validations to be applied 
    :param choice_fields:if model contains multiselectfield
    :return:model specific serializer with dynamic binding of validation hooks
    """

    class GenericSerializer(serializers.ModelSerializer):
        # checkboxgroup = fields.MultipleChoiceField(choices=choices1)
        locals().update(choice_fields)

        class Meta:
            # locals().update(validators_d)
            model = model_arg
            fields = '__all__'

        def create(self, validated_data):
            obj_create = self.Meta.model
            if 'files' in validated_data.keys():
                files = validated_data.pop('files')
                created_obj = obj_create.objects.create(**validated_data)
                if created_obj is not None:
                    for file in files:
                        MasterFiles.objects.create(name=file.get('filename'), file=file.get('file'),
                                                   app=file.get('app'), model=file.get('model'),
                                                   related_id=created_obj.pk, related_field=file.get('field'))
                        created_obj.is_filefield = True
                        created_obj.save()
                        if MASTER_FILES_MOSS_UPLOAD:
                            dms_service = MossDms(MOSS_BASE_URL, MOSS_USERNAME, MOSS_PASSWORD)

                            file_path = created_obj.file.path
                            file_name = file_path.split('\\')[-1]
                            status, name, path = dms_service.upload(RELATIVE_FOLDER_TO_UPLOAD_URL,
                                                                    created_obj.file, file_name)
                            created_obj.moss_url = path
                            created_obj.save()

                return created_obj
            created_obj = obj_create.objects.create(**validated_data)
            return created_obj

        def update(self, instance, validated_data):
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            return instance

        def to_internal_value(self, request_data):
            errors = {}
            ret = super(GenericSerializer, self).to_internal_value(request_data)
            current_user = self.context['request'].user
            codename = self.context['codename']
            files = self.context['files']
            if current_user.groups.filter(permissions__codename=codename).exists():
                if files:
                    ret.update({"files": files})
                return ret
            if errors:
                raise ValidationError(errors)
            return ret

    return GenericSerializer


def GenericSerializerField(model_arg, model_validations, choice_fields, restrict_fields):
    """
    Special Field Serializer
    Only for PUT method
    :param model_arg:model for serializer
    :param model_validations:model validations to be applied 
    :param choice_fields:if model contains multiselectfield
    :param restrict_fields:restrict the fields to be edit
    :return:model specific serializer with dynamic binding of validation hooks
    """

    class GenericSerialField(serializers.ModelSerializer):
        locals().update(choice_fields)

        class Meta:
            # locals().update(validators_d)
            model = model_arg
            fields = '__all__'
            locals().update(restrict_fields)
            # extra_kwargs = {'created_by' :{'read_only' : True}}

        def create(self, validated_data):
            obj_create = self.Meta.model
            return obj_create.objects.create(**validated_data)

        def update(self, instance, validated_data):
            is_file_field = validated_data.pop('is_file_field', False)
            old_files = validated_data.pop('old_files', None)
            app = validated_data.pop('app')
            model_name = validated_data.pop('model_name')
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            if is_file_field:
                if old_files:
                    all_files = MasterFiles.objects.filter(app=old_files['app'], model=old_files['model'],
                                                           related_id=instance.pk).values_list('uid', flat=True)
                    to_remove = list(set(all_files) - set(old_files['ids']))
                    MasterFiles.objects.filter(app=old_files['app'], model=old_files['model'],
                                               related_id=instance.pk, uid__in=to_remove).delete()
                elif not old_files:
                    MasterFiles.objects.filter(related_id=instance.pk, app=app, model=model_name).delete()
                    instance.is_filefield = False
                    instance.save()

                if 'files' in validated_data.keys():
                    files = validated_data.pop('files')
                    if instance and files:
                        for file in files:
                            MasterFiles.objects.create(name=file.get('filename'), file=file.get('file'),
                                                       app=file.get('app'), model=file.get('model'),
                                                       related_id=instance.pk, related_field=file.get('field'))
                            instance.is_filefield = True
                            instance.save()
                            if MASTER_FILES_MOSS_UPLOAD:
                                dms_service = MossDms(MOSS_BASE_URL, MOSS_USERNAME, MOSS_PASSWORD)
                                file_path = instance.file.path
                                file_name = file_path.split('\\')[-1]
                                status, name, path = dms_service.upload(RELATIVE_FOLDER_TO_UPLOAD_URL,
                                                                        instance.file, file_name)
                                instance.moss_url = path
                                instance.save()

            return instance

        def to_internal_value(self, request_data):
            is_file_field = self.context['is_file_field']
            current_user = self.context['request'].user
            codename = self.context['codename']
            files = self.context['files']
            old_files = self.context['old_files']
            app = self.context['app']
            model_name = self.context['model_name']
            ret = super(GenericSerialField, self).to_internal_value(request_data)
            if self.context['model'].created_by == current_user.username:
                if files or old_files:
                    ret.update({"files": files, "old_files": old_files, "is_file_field": is_file_field})
                ret.update({'app': app, 'model_name': model_name, "is_file_field": is_file_field})
                return ret
            if current_user.groups.filter(permissions__codename=codename).exists():
                if files or old_files:
                    ret.update({"files": files, "old_files": old_files, "is_file_field": is_file_field})
                ret.update({'app': app, 'model_name': model_name, "is_file_field": is_file_field})
                return ret

    return GenericSerialField


def NestedSerializer(model_arg, related_fields, fields_to_fetch):
    """
    Relational Serializer for ONE to MANY
    for models having related fields
    :param model_arg:model for serializer
    :param related_fields:the related fields of the model
    :param fields_to_fetch:display only subset of fields
    :return:model specific serializer 
    """

    class Testrelationserializer(serializers.ModelSerializer):
        locals().update(related_fields)

        class Meta:
            model = model_arg
            fields = fields_to_fetch

        def create(self, validated_data):
            obj_create = self.Meta.model
            return obj_create.objects.create(**validated_data)

    return Testrelationserializer


def GenericTrackSerializer(model_arg):
    """
    Supported serializer for ONE to MANY relations
    i.e cities = Cityserializer(many=TRUE)
    :param model_arg:model for serializer
    :return:model specific serializer
    """

    class GenericSerializer(serializers.ModelSerializer):
        class Meta:
            model = model_arg
            fields = ['name']

    return GenericSerializer


def ReverseStringSerializer(model_arg, keys):
    """
    Serializer for relation MANY to ONE Foreignkey Value Serializer
    USED StringRelatedField(many = TRUE)
    :param model_arg:model for serializer
    :param keys:dynamic mapping for nested serializer
    :return:model specific serializer
    """

    class GenericSerializer(serializers.ModelSerializer):
        locals().update(keys)

        def get_files(self, instance):
            app = model_arg._meta.app_label
            model = model_arg._meta.model_name
            decorators = list(MasterFiles.objects.filter(app__iexact=app, model__iexact=model, related_id=instance.pk)
                              .values_list('related_field', flat=True).distinct())
            info = dict()
            for deco in decorators:
                objs = MasterFiles.objects.filter(app__iexact=app, model__iexact=model, related_id=instance.pk, related_field=deco)
                if objs:
                    serial = MasterFilesSerializer(objs, many=True)
                    info[deco] = serial.data
            if info:
                return info
            else:
                return None

        def to_representation(self, instance):
            model = model_arg._meta.model_name
            ret = super(GenericSerializer, self).to_representation(instance)
            restrict_fields(ret)
            current_user = self.context['request'].user
            user_groups = [i.name for i in current_user.groups.all()]
            for field_name, field_value in sorted(ret.items()):
                for j in user_groups:
                    if current_user.groups.filter(
                            permissions__codename=FORMAT_PERMISSION_CODENAME['data_restrict'].format(j, model.lower(),
                                                                                                     field_name)).exists():
                        if field_value in DATA_RESTRICT_PERMISSIONS[FORMAT_PERMISSION_CODENAME['data_restrict'].format(j, model.lower(), field_name)]:
                            return None
                if current_user.groups.filter(permissions__codename=FORMAT_PERMISSION_CODENAME['view']
                        .format(field_name)).exists():
                    continue
                if current_user.groups.filter(permissions__codename=FORMAT_PERMISSION_CODENAME['restrict']
                        .format(field_name)).exists():
                    ret.pop(field_name)
            return ret

        class Meta:
            model = model_arg
            fields = '__all__'

    return GenericSerializer


def ReverseNestedSerializer(model_arg, serial_fields):
    """
    Reverese serializer for MANY to ONE for Output
    Nested Json
    :param model_arg:model for serializer
    :return:model specific serializer
    """

    class GenericSerializer(serializers.ModelSerializer):
        locals().update(serial_fields)
        class Meta:
            depth = 10
            model = model_arg
            fields = '__all__'

    return GenericSerializer


def dropdownSerialzer(model_arg):
    """
    Reverese serializer for MANY to ONE for Output
    Nested Json
    :param model_arg:model for serializer
    :return:model specific serializer
    """

    class GenericSerializer(serializers.ModelSerializer):
        # locals().update(keys)
        class Meta:
            model = model_arg
            fields = ["name", model_arg._meta.pk.name]

    return GenericSerializer


class MasterFilesSerializer(serializers.ModelSerializer):

    class Meta:
        model = MasterFiles
        fields = '__all__'


def ExcelSerializer(model_arg, choice_fields):
    class GenericSerializer(serializers.ModelSerializer):
        locals().update(choice_fields)

        class Meta:
            model = model_arg
            fields = '__all__'

        def create(self, validated_data):
            obj_create = self.Meta.model
            return obj_create.objects.create(**validated_data)

        def update(self, instance, validated_data):
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            return instance

    return GenericSerializer