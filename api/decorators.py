"""
Create Decorators for Various
Requests methods i.e GET,POST,PUT,DELETE
"""
import functools
from api.logger_directory import requests_logger, user_logger

REQ_LOGS = requests_logger()
USER_LOGS = user_logger()


def SpecificViewDecorator(func):
    """
    Decorator for GenericMaster Class to Differentitiate
    Specific data requests and to fetch the Common Variables Commonly
    :param func: function on which applied 
    :return: function with wrapper  
    """

    @functools.wraps(func)
    def wrapper(self, request, **kwargs):
        app = kwargs.get('app')
        model = kwargs.get('model')
        id = kwargs.get('id')
        if app and model and id:
            return func(self, request, app, model, id)
        else:
            return func(self, request, app, model)

    return wrapper


def ListViewDecorator(func):
    """
     Decorator for ListView Class
    to fetch all the Common variabls Commonly
    :param func: function on which applied 
    :return: function with wrapper 
    """

    @functools.wraps(func)
    def wrapper(self, request, **kwargs):
        app = kwargs.get('app')
        model = kwargs.get('model')
        # list_arg = kwargs.get('list')
        if app and model:  # and list_arg:
            return func(self, request, app, model)
        else:
            return func(self, request, app, model)

    return wrapper


def logger_create(func):
    """
    Common Decorator for Both view Classes
    to create LOGS in the File
    :param func:function on which applied 
    :return: function with wrapper 
    """

    @functools.wraps(func)
    def wrap(self, request, *args, **kwargs):
        if kwargs.get('id'):
            REQ_LOGS.info(
                " {} by -- {} for id -- {} -- IP -- {} ".format(func.__name__.upper(),
                                              str(request.user), str(kwargs.get('id')), str(request.META.get('REMOTE_ADDR'))))
        elif kwargs.get('list') and func.__name__.upper() == "POST":
            REQ_LOGS.info("Conditional {} by -- {} -- IP -- {} ".format(func.__name__.upper(), str(request.user), str(request.META.get('REMOTE_ADDR'))))
        else:
            REQ_LOGS.info(" {} by -- {} -- IP -- {}".format(func.__name__.upper(), str(request.user), str(request.META.get('REMOTE_ADDR'))))
        return func(self, request, *args, **kwargs)

    return wrap


def user_logger_create(func):
    """
    Decorator for Login And Logout View Class to create logs of the
    New and Authenticated User
    :param func: function on which applied 
    :return: function with wrapper
    """

    @functools.wraps(func)
    def wrap(self, request, *args, **kwargs):
        req_dict = request.data
        USER_LOGS.info(
            "Data by {} for Incoming Login Request by -- {} -- IP -- {}".format(func.__name__.upper(), str(req_dict['username']), str(request.META.get('REMOTE_ADDR'))))
        REQ_LOGS.info(
            "Data by {} for Incoming Login Request by -- {} -- IP -- {}".format(func.__name__.upper(), str(req_dict['username']), str(request.META.get('REMOTE_ADDR'))))
        return func(self, request, *args, **kwargs)

    return wrap
