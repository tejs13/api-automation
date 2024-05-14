import json
from datetime import datetime
from collections import defaultdict
import os
import pandas as pd
from django.db import transaction
from reversion import revisions as reversion
from django.conf import settings
from django.utils import timezone
from api.serializers import ExcelSerializer
from api.config_app import PREDEFINED_FIELD_TYPES
from rest_framework import serializers

from workflow.services import approval_workflow

DATE_INPUT_FORMAT = settings.__dict__['_wrapped'].__dict__['DATE_INPUT_FORMAT']
DATE_TIME_INPUT_FORMAT = settings.__dict__['_wrapped'].__dict__['DATE_TIME_INPUT_FORMAT']
TIME_INPUT_FORMAT = settings.__dict__['_wrapped'].__dict__['TIME_INPUT_FORMAT']
WORKFLOW_MODEL_LIST = settings.__dict__['_wrapped'].__dict__['WORKFLOW_MODEL_LIST']

def get_filename():
    """
    Creates file name based on timestamp
    :return: Name of file
    :rtype: str
    """
    now = datetime.now()
    now = str(now)
    to_replace = [' ', '-', ':', '.']
    for each in to_replace:
        now = now.replace(each, '_')
    return now + '.xlsx'


class ExcelImportExport:
    """
    This class takes json data as an argument and converts it into Pandas DataFrame and then exports to Excel file.
    """
    def __init__(self, logger):
        self.logger_excel = logger

    def export_to_excel(self, data, primary_key):
        """
        This function will generate excel file based on the input of json data and sends back post request with
        absolute file path of the generated excel sheet
        :param data: JSON Data from UI
        :type data: dict
        :return: None
        :rtype: None
        """
        data = json.loads(data)
        columnList = data['columns']
        self.logger_excel.info(columnList)

        df = []
        for each in data['results']:
            keys = list(columnList)
            for key in keys:
                if type(each[key]) is dict:
                    each[key] = each[key][list(each[key].keys())[0]]
                elif type(each[key]) is list and len(each[key]) >= 0:
                    # each[key] = each[key][0][list(each[key][0].keys())[0]]
                    each[key] = len(each[key])
            df.append(each)

        temp_dict = defaultdict(list)
        self.logger_excel.info(df)
        for each in df:
            for key, value in each.items():
                if key in columnList:
                    temp_dict[key].append(value)
                elif columnList is None:
                    temp_dict[key].append(value)
        df = pd.DataFrame.from_dict(dict(temp_dict))
        df = df[columnList]
        file_name = get_filename()
        try:
            df.set_index(primary_key, inplace=True)
        except Exception as e:
            pass
        df.columns = map(str.upper, df.columns)
        df.to_excel(file_name, index=False)
        self.logger_excel.info("Excel sheet generated for input json data")
        # post_url_data(file_name)
        file = None
        with open(file_name, 'rb') as f:
            file = f.readlines()
        os.remove(file_name)
        return file


    def import_excel(self, excel_file, unique_keys, model, request, app, model_name):
        """
        This function imports uploaded Excel Sheet into Database using Django Models Object.
        :param excel_file: Uploaded excel file
        :type excel_file: file
        :param unique_keys: Primary Key dictionary with Key as Column name and Value as column index
        :type unique_keys: dict
        :param model: Django Model which will be used to Update/Insert data into Database
        :type model: models
        :return: Returns list of inserted data (dict) and updated data (dict)
        :rtype: list
        """
        try:
            excel_data = pd.read_excel(excel_file)
            message = ''
            # excel_data = pd.read_csv(excel_file)
            excel_data.columns = map(str.lower, excel_data.columns)
            choice_fields = {}
            excel_columns = list(excel_data.columns)
            final_fields = [field for field in model._meta.get_fields() if field.name in excel_columns]
            for field in final_fields:
                if field.get_internal_type() == PREDEFINED_FIELD_TYPES["DateField"]:
                    choice_fields[field.name] = serializers.DateField(input_formats=DATE_INPUT_FORMAT)
                    excel_data[field.name] = pd.to_datetime(excel_data[field.name], format=DATE_INPUT_FORMAT[0])
                    excel_data[field.name] = excel_data[field.name].dt.date
                if field.get_internal_type() == PREDEFINED_FIELD_TYPES["DateTimeField"]:
                    choice_fields[field.name] = serializers.DateTimeField(input_formats=DATE_TIME_INPUT_FORMAT)
                    if field.name != 'created_date' and field.name != 'last_updated_date':
                        excel_data[field.name] = pd.to_datetime(excel_data[field.name], format=DATE_TIME_INPUT_FORMAT[0])
                if field.get_internal_type() == PREDEFINED_FIELD_TYPES["TimeField"]:
                    choice_fields[field.name] = serializers.TimeField(input_formats=TIME_INPUT_FORMAT)
                if field.get_internal_type() == PREDEFINED_FIELD_TYPES["CharField"] and \
                        field.name != 'created_by' and \
                        field.name != 'last_updated_by':
                    excel_data[field.name] = [str(each) for each in excel_data[field.name]]
                if field.get_internal_type() == PREDEFINED_FIELD_TYPES["CharField"] and \
                        field.name != 'created_by' and \
                        field.name != 'last_updated_by':
                    excel_data[field.name] = [str(each) for each in excel_data[field.name]]
                if field.get_internal_type() == PREDEFINED_FIELD_TYPES["IntegerField"]:
                    excel_data[field.name] = [int(each) for each in excel_data[field.name]]

            serializer = ExcelSerializer(model, choice_fields)
            cols = list(excel_data.columns)
            updated_data = []
            inserted_data = []
            failed_data = []
            username = str(request.user)

            for each in range(len(excel_data)):
                if unique_keys:
                    filter_args = {
                        col_name: excel_data.loc[each][cols[col_index]]
                        for col_name, col_index in unique_keys.items()
                    }
                    # Check required fields
                    error_list = []
                    for key, value in filter_args.items():
                        if not str(value) and str(value) != 'None':
                            error_list.append(key)
                    if len(error_list) > 0:
                        return 'Required Fields cannot be empty -> %s' % error_list
                    # excel_data['date_field'].astype(datetime.date)
                    if model.objects.filter(**filter_args).exists():
                        temp_object = model.objects.get(**filter_args)
                        data = excel_data.loc[each].to_dict()
                        data['last_updated_by'] = username
                        data['is_deleted'] = False
                        data['is_active'] = True
                        data['last_updated_date'] = datetime.now()
                        data['status'] = 'Draft'
                        # data['date_field'] = datetime.date(data['date_field'])
                        # data = {key: str(value) for key, value in data.items()}
                        serializer_data = serializer(temp_object, data=data, partial=True)
                        if serializer_data.is_valid():
                            with transaction.atomic(), reversion.create_revision():
                                reversion.set_user(request.user)
                                reversion.set_comment(request.method)
                                reversion.set_date_created(date_created=datetime.now())
                                createdObj = serializer_data.save()
                                updated_data.append(excel_data.loc[each].to_dict())
                                if model_name.lower() in WORKFLOW_MODEL_LIST:
                                    request_status, workflow_completed = approval_workflow(app=app, model=model_name.lower(),
                                                                                           pk=createdObj.pk,
                                                                                           action='Init',
                                                                                           remarks='initiated',
                                                                                           request=request,
                                                                                           requesting_approvers=request.data.
                                                                                           get('approval_type'))
                                    createdObj.status = request_status
                                    createdObj.is_approved = workflow_completed
                                    createdObj.save()
                        else:
                            temp_message = list(serializer_data.errors.keys())[0] + ': ' + \
                                           list(serializer_data.errors.values())[0][0]
                            if not message.__contains__(temp_message):
                                message = message + temp_message + ', '
                                self.logger_excel.error('Error while importing from Excel: %s' % serializer_data.errors)
                            failed_data.append(excel_data.loc[each].to_dict())

                    else:
                        data = excel_data.loc[each].to_dict()
                        data['created_by']=username
                        data['created_date']=datetime.now()
                        data['last_updated_date']=datetime.now()
                        data['last_updated_by']=username
                        data['status'] = 'Draft'
                        serializer_data = serializer(data=data)
                        if serializer_data.is_valid():
                            with transaction.atomic(), reversion.create_revision():
                                reversion.set_user(request.user)
                                reversion.set_comment(request.method)
                                reversion.set_date_created(date_created=datetime.now())
                                createdObj = serializer_data.save()
                                if model_name.lower() in WORKFLOW_MODEL_LIST:
                                    request_status, workflow_completed = approval_workflow(app=app,
                                                                                           model=model_name.lower(),
                                                                                           pk=createdObj.pk,
                                                                                           action='Init',
                                                                                           remarks='initiated',
                                                                                           request=request,
                                                                                           requesting_approvers=request.data.
                                                                                           get('approval_type'))
                                    createdObj.status = request_status
                                    createdObj.is_approved = workflow_completed
                                    createdObj.save()
                                inserted_data.append(excel_data.loc[each].to_dict())
                        else:
                            temp_message = list(serializer_data.errors.keys())[0] + ': ' + \
                                           list(serializer_data.errors.values())[0][0]
                            if not message.__contains__(temp_message):
                                message = message + temp_message + ', '
                                self.logger_excel.error('Error while importing from Excel: %s' % serializer_data.errors)
                            failed_data.append(excel_data.loc[each].to_dict())
                else:
                    data = serializer(data=excel_data.loc[each].to_dict())
                    if data.is_valid():
                        data.save()
                        inserted_data.append(excel_data.loc[each].to_dict())
                    else:
                        failed_data.append(excel_data.loc[each].to_dict())
            return [inserted_data, updated_data, failed_data, message]
        except Exception as e:
            self.logger_excel.exception(e)
            raise e

    def get_latest_db_data(self, data1, excel_data, primary_key):
        """
        Gets all the records from database of input table name and assumes first column as primary key
        and also returns name of primary key column for further usage.
        :param table_name: Name of table to get data
        :type table_name: str
        :return: Retrieved data from database as DataFrame
        :rtype: pandas.core.frame.DataFrame, str
        """

        return self.get_df_difference(data1, excel_data, primary_key)

    def get_df_difference(self, db_data, excel_data, primary_key):
        """
        Gets the difference between two DataFrame using pandas merge function and lambda expression
        :param primary_key: Primary key of the data from database which is first column of the dataframe
        :type primary_key: str
        :param db_data: Database table data as DataFrame
        :type db_data: pandas.core.frame.DataFrame
        :param excel_data: Excel file data as DataFrame
        :type excel_data: pandas.core.frame.DataFrame
        :return: None
        :rtype: None
        """

        db_data = db_data.astype(excel_data.dtypes.to_dict())

        difference = db_data.merge(
            excel_data, indicator=True, how='right').loc[lambda x: x['_merge'] != 'both']
        return self.check_excel_data(difference, db_data, primary_key)

    def check_excel_data(self, difference_df, db_data, primary_key):
        """
        This method checks rows to update and insert into database.
        Separate function call is made for both insert and update operations
        :param primary_key: Primary key of the data from database which is first column of the dataframe
        :type primary_key: str
        :param difference_df: Difference between database data and excel data
        :type difference_df: pandas.core.frame.DataFrame
        :param db_data: Data from database
        :type db_data: pandas.core.frame.DataFrame
        :return: None
        :rtype: None
        """

        try:
            return_list = []
            new_id = list(difference_df[primary_key])
            old_id = list(db_data[primary_key])
            insert_id_data = [each for each in new_id if each not in old_id]
            insert_df = [pd.DataFrame(
                difference_df[difference_df[primary_key] == each]) for each in insert_id_data]
            if insert_df:
                insert_data = pd.concat(insert_df)
                self.logger_excel.info(
                    "No. of data to insert : %s" % len(insert_df))
                insert_data_dict = insert_data.to_dict(orient='records')
                return_list.append(insert_data_dict)
                # self.db_operations('insert', insert_data, primary_key)
            else:
                self.logger_excel.info("No new Data to insert")
            update_id_data = [each for each in new_id if each in old_id]
            update_df = [pd.DataFrame(
                difference_df[difference_df[primary_key] == each]) for each in update_id_data]
            if update_df:
                update_data = pd.concat(update_df)
                self.logger_excel.info(
                    "No. of data to update : %s" % len(update_df))
                update_data_dict = update_data.to_dict(orient='records')
                return_list.append(update_data_dict)
                # self.db_operations('update', update_data, primary_key)
            else:
                self.logger_excel.info("No Data to update")
            return return_list
        except Exception as e:
            self.logger_excel.exception(e)


if __name__ == '__main__':
    LOGGER_EXCEL = init_logging(log_name='Excel_ImportExport', enable_mailing=False)
    ExcelImportExport(LOGGER_EXCEL)
