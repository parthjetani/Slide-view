from django.db import models
from django.conf import settings
import os
from uuid import uuid4
from django.utils.deconstruct import deconstructible
from authentication.models import CustomUser

@deconstructible
class UploadToPathAndRename(object):

    def __init__(self, path):
        self.sub_path = path

    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]
        filename = '{}.{}'.format(uuid4().hex, ext)
        # return the whole path to the file
        return os.path.join(self.sub_path, filename)


class Folder(models.Model):
    organization = models.CharField(max_length=100, null=True)
    Name = models.CharField(max_length=100)
    Created = models.DateField(auto_now_add=True)
    Modified = models.DateField(auto_now=True)
    Parent = models.ForeignKey('self', null=True, related_name='parent', on_delete=models.SET_NULL)

    def __str__(self):
        return self.Name


class Slide(models.Model):
    organization = models.CharField(max_length=100, null=True)
    SlideType_choices = ((1, 'DICOM'), (2, 'openslide'))
    Name = models.CharField(max_length=50)
    ScannedBy = models.CharField(max_length=50, blank=True)
    ScannedDate = models.DateField(blank=True)
    InsertedBy = models.CharField(max_length=50, blank=True)
    InsertedDate = models.DateField(blank=True)
    SlideType = models.IntegerField(choices=SlideType_choices)    
    UrlPath = models.CharField(max_length=500)
    LabelUrlPath = models.CharField(max_length=500)
    Group = models.IntegerField(default=0)
    GroupName = models.CharField(max_length=100, default="Default Group")
    Annotations = models.BooleanField(default=False)
    Folder = models.ForeignKey(Folder, on_delete=models.CASCADE)
    Filesize = models.FloatField(default=0)
    Tag = models.CharField(max_length=50, blank=True)
    CopyOf = models.ForeignKey('self', null=True, related_name='copy', on_delete=models.SET_NULL)
    CaseNo = models.CharField(max_length=50, blank=True)
    
    class Meta:
        ordering = ['UrlPath']

    def __str__(self):
        return self.Name

class Annotation(models.Model):
    Slide_Id = models.ForeignKey(Slide, on_delete=models.CASCADE)
    Json = models.TextField()
    AnnotationText = models.TextField()
    Type = models.CharField(max_length=10,blank=False)


class Activity(models.Model):
    Slide_Id = models.ForeignKey(Slide, on_delete=models.CASCADE)
    Saved = models.BooleanField(default=False)
    LastAccessed = models.DateTimeField()