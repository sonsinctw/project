from django.urls import path
from . import views
from .views import check_connection_view

urlpatterns = [
    path('accounts/login/', views.login, name='login'),
    path('', views.index_view, name='index'),
    path('logout/', views.logout, name='logout'),
    path('add/', views.add_product_view, name='add'),
    path('edit/<int:id>/', views.edit_product_view, name='edit'),
    path('delete/<int:id>/', views.delete_product_view, name='delete'),
    path('<int:id>/', views.view_product_view, name='view_product'),
    path('product_detail/<int:id>/', views.product_detail_view, name='product_detail'),
    path('read_barcode/', views.read_barcode_view, name='read_barcode'),
    path('move_product/<int:id>/', views.move_product_view, name='move_product'),
    path('update_shelf/<int:id>/', views.update_shelf_view, name='update_shelf'),
    path('update_status/<int:id>/', views.update_status_view, name='update_status'),  
    path('history/', views.history_view, name='history'),
    path('clear_history/', views.clear_history_view, name='clear_history'),
    path('check_connection/', check_connection_view, name='check_connection'),
    path('change_ip/', views.change_ip_view, name='change_ip'),

]
