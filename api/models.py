from django.db import models

class BaseModel(models.Model):

    status = models.CharField(db_column='STATUS', default="Draft", max_length=100)
    is_approved = models.BooleanField(db_column='IS_APPROVED', default=False)
    is_active = models.BooleanField(db_column='IS_ACTIVE', blank=True, null=True,
                                    default=True)  # Field name made lowercase.

    is_deleted = models.BooleanField(db_column='IS_DELETED', blank=True, null=True,
                                     default=False)  # Field name made lowercase.
    created_by = models.CharField(db_column='CREATED_BY', max_length=50, blank=True,
                                  null=True)  # Field name made lowercase.
    created_date = models.DateTimeField(db_column='CREATED_DATE', auto_now_add=True)  # Field name made lowercase.
    last_updated_by = models.CharField(db_column='LAST_UPDATED_BY', max_length=50, blank=True,
                                       null=True)  # Field name made lowercase.
    last_updated_date = models.DateTimeField(db_column='LAST_UPDATED_DATE', auto_now=True)  # Field name made lowercase.

    class Meta:
        abstract = True

class MasterFiles(models.Model):
    uid = models.BigAutoField(db_column='FILE_UID', primary_key=True)
    name = models.CharField(db_column='FILE_NAME', max_length=2000)
    status = models.CharField(db_column='FILE_STATUS', default="done", max_length=200)
    file = models.FileField(db_column='FILE', upload_to='MASTER_FILES/%Y/%m/%d/', blank=True, null=True)
    moss_url = models.CharField(db_column='MOSS_URL', max_length=2000, blank=True, null=True)
    app = models.CharField(db_column='app', max_length=200)
    model = models.CharField(db_column='model', max_length=500)
    related_id = models.IntegerField(db_column='RELATED_ID')
    related_field = models.CharField(db_column='RELATED_FIELD', max_length=200)


    class Meta:
        db_table = "MASTER_FILES"
        app_label = "api"

