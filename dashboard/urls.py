from django.urls import path
from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^slide/(?P<slide_id>\d+)/$', views.slide),
    url(r'^slide/(?P<slide_id>\d+)/thumbnail/$', views.gen_thumbnail_url),
    url(r'^slide/(?P<slide_id>\d+)/fullthumbnail/$', views.get_thumbnail),
    url(r'^slide/(?P<slide_id>\d+)/barcode/$', views.get_barcode),
    url(r'^slide/(?P<slide_id>\d+)/label/$', views.gen_label),
    url(r'^slide/(?P<slide_id>\d+)/download/$', views.download_slide,name="slide-download"),
    url(r'^slide/(?P<slide_id>\d+)/delete/$', views.delete_slide),
    url(r'^slide/(?P<slide_id>\d+)/delete/confirm/$', views.delete_confirm_slide),
    url(r'^slide/(?P<slide_id>\d+)/group/$', views.get_group_list),
    url(r'^slide/(?P<slide_id>\d+)/property/$', views.get_property),
    url(r'^slide/(?P<slide_id>\d+)/name/$', views.get_name),
    url(r'^slide/(?P<slug>\d+).dzi$', views.dzi),
    url(r'^slide/(?P<slug>\d+).dzi.json$', views.properties),
    url(r'^slide/(?P<slug>\d+)_files/(?P<level>\d+)/(?P<col>\d+)_(?P<row>\d+)\.(?P<slideformat>jpeg|png)$', views.dztile),
    url(r'^slide/(?P<slug>\d+)_map/(?P<level>\d+)/(?P<col>\d+)_(?P<row>\d+)\.(?P<slideformat>jpeg|png)$', views.gmtile),
    url(r'^slide/annotation/add$', views.add_annotation),
    url(r'^slide/annotation/edit/(?P<id>\d+)$', views.edit_annotation),
    url(r'^slide/annotation/delete/(?P<id>\d+)$', views.delete_annotation),
    url(r'^slide/annotation/(?P<slide_id>\d+)$', views.get_annotation),
    path('', views.index, name='index'),
    path('my_folders/', views.my_folders, name='my_folders'),
    path('my_slides/', views.my_slides, name='my-slides'),
]
