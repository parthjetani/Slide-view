from django.urls import path
from . import views


slide_patterns =[
    path('slides/<str:action>/', views.SlidesView.as_view(), name='slide-search'),

]

urlpatterns = [
    path('folder/new', views.folder_create, name='folder_create'),
    path('folder/content', views.folder_content, name='folder_content'),
    path('folder/parent', views.folder_parents, name='folder_parents'),
    path('folder/get', views.folder_get, name='folder_get'),
    path('folder/edit', views.folder_edit, name='folder_edit'),
    path('folder/delete', views.folder_delete, name='folder_delete'),
    path('folder/search', views.folder_search, name='folder_search'),
    path('file/new', views.slide_upload, name='slide_upload'),
    path('file/exist', views.file_exist, name='file_exist'),
    path('file/valid', views.valid_filename, name='valid_filename'),
    path('file/edit', views.file_edit, name='file_edit'),
    path('file/get', views.file_get, name='file_get'),
    path('file/delete', views.file_delete, name='file_delete'),
    path('file/delete-multiple', views.bulk_files_delete, name='bulk_files_delete'),
    path('file/copy', views.file_copy, name='file_copy'),
    path('folder', views.folder_structure, name='folder_structure'),
    path('folder-structure', views.folder_structure_for_my_folder, name='folder_structure_for_my_folder'),
    path('cases', views.cases, name='cases'),
    path('only-slide/<int:pk>', views.only_slide, name='cases'),
    path('only-folder', views.only_folder, name='only-folder'),
    
    path('storage', views.storage_info, name='storage_info'),
    path('', views.index, name='index'),
] + slide_patterns