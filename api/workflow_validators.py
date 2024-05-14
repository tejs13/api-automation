from django.conf import settings

WORKFLOW_MODEL_LIST = settings.__dict__['_wrapped'].__dict__['WORKFLOW_MODEL_LIST']
GROUP_WISE_STATUS_MAPPING = settings.__dict__['_wrapped'].__dict__['GROUP_WISE_STATUS_MAPPING']
APPROVAL_GROUPS = settings.__dict__['_wrapped'].__dict__['APPROVAL_GROUPS']

def check_edit_allow(model_name, obj):

    if model_name.lower() in WORKFLOW_MODEL_LIST:
        if obj.is_approved:
            return False
        else:
            return True
    else:
        return True


def get_pending_for_group_user(model_obj, request):
    model_name = model_obj._meta.model.__name__
    groups = request.user.groups.all()
    approval_groups = [group.name for group in groups if group.name in APPROVAL_GROUPS]
    final_groups = [group.name for group in groups if group.name in GROUP_WISE_STATUS_MAPPING]
    if model_name.lower() in WORKFLOW_MODEL_LIST:
        final_status = []
        [final_status.extend(GROUP_WISE_STATUS_MAPPING[group]) for group in final_groups]
        is_pending_requests_exists = model_obj.objects.filter(is_active=True, status__in=final_status, is_deleted=False).order_by('-pk')
        if is_pending_requests_exists:
            return is_pending_requests_exists
        else:
            return model_obj.objects.none()
    else:
        return model_obj.objects.filter(is_active=True, is_deleted=False).order_by('-pk')

