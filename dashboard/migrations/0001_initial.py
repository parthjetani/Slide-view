# Generated by Django 3.1.6 on 2021-02-26 18:18

import dashboard.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Folder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Name', models.CharField(max_length=100)),
                ('Created', models.DateField(auto_now_add=True)),
                ('Modified', models.DateField(auto_now=True)),
                ('Path', models.CharField(max_length=500)),
            ],
        ),
        migrations.CreateModel(
            name='Slide',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Name', models.CharField(max_length=50)),
                ('ScannedBy', models.CharField(blank=True, max_length=50)),
                ('ScannedDate', models.DateField(blank=True)),
                ('InsertedBy', models.CharField(blank=True, max_length=50)),
                ('InsertedDate', models.DateField(blank=True)),
                ('SlideType', models.IntegerField(choices=[(1, 'DICOM'), (2, 'openslide')])),
                ('UrlPath', models.FileField(max_length=500, upload_to='media/uploads/slides/')),
                ('LabelUrlPath', models.ImageField(default='/mnt/d/projects/slide_management_app/slide_management/static/labels/placeholder.png', max_length=500, upload_to=dashboard.models.UploadToPathAndRename('/mnt/d/projects/slide_management_app/slide_management/static/labels'))),
                ('Group', models.IntegerField(default=0)),
                ('GroupName', models.CharField(default='Default Group', max_length=100)),
                ('Annotations', models.BooleanField(default=False)),
                ('Folder_Id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dashboard.folder')),
            ],
            options={
                'ordering': ['UrlPath'],
            },
        ),
        migrations.CreateModel(
            name='Annotation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Json', models.TextField()),
                ('AnnotationText', models.TextField()),
                ('Type', models.CharField(max_length=10)),
                ('Slide_Id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dashboard.slide')),
            ],
        ),
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Saved', models.BooleanField(default=False)),
                ('LastAccessed', models.DateTimeField()),
                ('Slide_Id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dashboard.slide')),
            ],
        ),
    ]
