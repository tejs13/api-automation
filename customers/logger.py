import os

from django.conf import settings

customer_log = init_logging(log_name='CUSTOMER_LOG', log_level='DEBUG', enable_mailing=False,
                   rotation_criteria='time', rotate_interval=1, rotate_when='d',
                   backup_count=30, log_directory=os.path.join(settings.BASE_DIR, 'logs'))

customer_wishlist_log = init_logging(log_name='CUSTOMER_WISHLIST_LOG', log_level='DEBUG', enable_mailing=False,
                   rotation_criteria='time', rotate_interval=1, rotate_when='d',
                   backup_count=30, log_directory=os.path.join(settings.BASE_DIR, 'logs'))

customer_cart_log = init_logging(log_name='CUSTOMER_CART_LOG', log_level='DEBUG', enable_mailing=False,
                   rotation_criteria='time', rotate_interval=1, rotate_when='d',
                   backup_count=30, log_directory=os.path.join(settings.BASE_DIR, 'logs'))

draft_customer_signal_log = init_logging(log_name='DRAFT_CUSTOMER_SIGNAL_LOGS', log_level='DEBUG', enable_mailing=False,
                   rotation_criteria='time', rotate_interval=1, rotate_when='d',
                   backup_count=30, log_directory=os.path.join(settings.BASE_DIR, 'logs'))

customer_signal_log = init_logging(log_name='CUSTOMER_SIGNAL_LOGS', log_level='DEBUG', enable_mailing=False,
                   rotation_criteria='time', rotate_interval=1, rotate_when='d',
                   backup_count=30, log_directory=os.path.join(settings.BASE_DIR, 'logs'))
