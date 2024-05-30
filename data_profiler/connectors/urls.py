from django.urls import path
from . import views

urlpatterns = [
    path('check_conn/',views.check_conn,name='check_conn'),
    path('', views.connectors, name="connectors"),
    path('conlist/',views.conlist,name='conlist'),
    path('selectdatabase/',views.selectdatabase,name='selectdatabase'),
    path('tablelist/', views.tablelist, name='tablelist'),
    path('select_table/',views.select_table,name = 'select_table'),
    path('selected_table/<str:selected_table>/', views.selected_table, name='selected_table'),
    path('select_conn/<int:connector_id>', views.select_conn, name='select_conn'),
    path('upload/', views.upload_file, name='upload_file'),
    path('table_view/', views.table_view, name='table_view'),
    path('charts_view/', views.charts_view, name='charts_view'),
    path('download-table/', views.download_table, name='download_table'),
    path('select/', views.select_connector, name='select_connector'),
    path('details/', views.connector_details, name='connector_details'),
    path('mypsql/', views.mypsql, name='mypsql'),
    path('show_all_tables/', views.show_all_tables, name='show_all_tables'),
    path('table/', views.show_table_data, name='show_table_data'),
    path('show_all_db/', views.show_all_db, name='show_all_db'),
]