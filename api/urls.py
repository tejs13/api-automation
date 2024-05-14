# pylint: disable = C0301,E0401,C0103
""" URLS for the API Access"""

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from api.views import GenericMaster, LoginView, LogoutView, \
    ListViewDetail, ReversionView, ModelVersions, ExcelExport, \
    ListFilter, SearchFilter, DownloadMasterFiles, ExcelImport, CopyDataView, BulkApprovalViewView, DashboardView



urlpatterns = [

    path('admin/', admin.site.urls),
    path('master/accounts/login/', auth_views.LoginView.as_view(), name="api"),
    # URL for login and Token Generation
    path('master/login', LoginView.as_view(), name='api'),
    # URL for logout
    path('master/logout', LogoutView.as_view(), name='api'),
    path('master/dynamic-dashboard', DashboardView.as_view(), name="api"),
    # path('master/auto_generate_sections', DashboardView.as_view(), name="api"),
    # URL to download master files
    path('master/download-file/<int:uid>', DownloadMasterFiles.as_view(), name='api'),
    # URL for all the LIST Operations
    path('master/<str:app>.<str:model>/list', ListViewDetail.as_view(), name='api'),
    path('master/<str:app>.<str:model>/import', ExcelImport.as_view(), name='excel'),
    path('master/<str:app>.<str:model>/export', ExcelExport.as_view(), name='excel'),
    # spicific operation URL
    path('master/<str:app>.<str:model>/<str:id>', GenericMaster.as_view(), name='api'),
    # URL for actual POST
    path('master/<str:app>.<str:model>', GenericMaster.as_view(), name='api'),
    # URL for  Nested Serializer
    path('master/<str:app>', GenericMaster.as_view(), name='api'),
    # URL for object versions

    path('master/versions/<str:app>.<str:model>/<str:id>', ReversionView.as_view(), name="api"),

    path('master/versions/<str:app>.<str:model>', ModelVersions.as_view(), name="api"),
    # url(r'^test_view/(?P<pk>\d+)$', Generic(registration).as_view(), name="h2"),
    path('master/filter/<str:app>.<str:model>', ListFilter.as_view(), name="api"),
    path('master/search/<str:app>.<str:model>', SearchFilter.as_view(), name="api"),
    path('master/copydata/<str:app>.<str:model>', CopyDataView.as_view(), name="api"),
    path('master/copydata/<str:app>.<str:model>/getdata', CopyDataView.as_view(), name="api"),
    path('master/bulk_approval/<str:app>.<str:model>', BulkApprovalViewView.as_view(), name="api"),



]
