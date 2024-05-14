"""
Metadata configuration constans
"""
LISTVIEW_CONST = {
    'DateTimeField': 'agDateColumnFilter',
    'IntegerField': 'agNumberColumnFilter',
    'DecimalField': "agDecimalColumnFilter",
    'DateField': 'agDateColumnFilter',
    'BooleanField' :None,
    'CharField' :None,
    'TextField' : None,
    'AutoField':None,
    'BigAutoField':None,
    'BigIntegerField' :None,
    'DurationField' :None,
    'EmailField':None,
    'FloatField' :None,
    'URLField' :None
}
FILTER_LIST_CONST = {
    'DateTimeField': 'datetime',
    'IntegerField': 'integer',
    'DecimalField': "integer",
    'DateField': 'date',
    'BooleanField' : 'radio',
    'CharField' : 'text',
    'TextField' : 'text',
    'AutoField':'integer',
    'BigIntegerField' :'integer',
    'DurationField' :'datetime',
    'EmailField':'text',
    'FloatField' :'integer',
    'URLField' :'text',
    'PositiveIntegerField': 'integer',
    'PositiveSmallIntegerFiel': 'integer',
    'PositiveBigIntegerField': 'integer',
    'BigAutoField': 'integer'

}

FILTER_FIELD_MAPPING = {
    'integer' : ['gt','lt','gte','lte'],
    'text' : ['icontains'],
    'date': ['before', 'after', 'exact'],
}
CONST_PRIMARY_KEY = 'primarykey'
CONST_FOREIGN_KEY = 'foreignkey'


APPMETA_CONST = {
    'sectionName': 'MASTERS',
    'icon': 'fa fa-th-list'
}

EXTRA_META_CONST = {
    'sectionName': 'FORMS',
    'icon': 'fa fa-wpforms'
}
