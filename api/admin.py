from django.contrib import admin
from django.contrib.auth.models import ContentType, Permission
from api.models import MasterFiles

admin.site.register(ContentType)
admin.site.register(Permission)
admin.site.register(MasterFiles)
