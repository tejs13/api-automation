from django.db.models.base import ModelBase
from django.apps import apps
from django.conf import settings

PROJECT_APPS = settings.__dict__['_wrapped'].__dict__['PROJECT_APPS']



def import_string(dotted_path):
    """
    Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import failed.
    """
    try:
        module_path, class_name = dotted_path.rsplit('.', 1)
    except ValueError as err:
        raise ImportError("%s doesn't look like a module path" % dotted_path) from err
    # module = import_module(module_path)
    try:
        return class_name
    except AttributeError as err:
        raise ImportError('Module "%s" does not define a "%s" attribute/class' % (
            module_path, class_name)
                          ) from err

def retrieve_correct_app(model):
    for app in PROJECT_APPS:
        try:
            model_obj = apps.get_model(app, model)
            if isinstance(model_obj, ModelBase):
                return app, model_obj
        except Exception as e:
            continue

def get_files_with_fields(files_dict, file_field_names, app, model, old_files=None):

    files_data = []
    old_files_dict = dict()
    if old_files:
        files_uids_to_keep = [i["uid"] for i in old_files]
        old_files_dict['ids'] = files_uids_to_keep
        old_files_dict['app'] = app
        old_files_dict['model'] = model
    if files_dict:
        for file in files_dict:
            info = dict()
            info['app'] = app
            info['model'] = model
            info['field'] = file[:-1]
            info['filename'] = files_dict[file][0].name
            info['file'] = files_dict[file][0]
            files_data.append(info)
        return files_data, old_files_dict
    else:
        return None, old_files_dict




