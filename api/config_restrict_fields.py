"""
restrict the model
fields for serializtion
"""

RESTRICT=[
    "password",
    "is_deleted",
    "name",

]

def restrict_fields(ret):
    """
    restrict the model fields
    from serialization
    :param ret: dict for model fields
    :return: dict for allowed only fields
    """
    restrict_list = [i for i in ret.keys() if i in RESTRICT]
    [ret.pop(i) for i in restrict_list]
    return ret



