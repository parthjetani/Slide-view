# Generated by Django 3.1.6 on 2021-02-27 15:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0003_remove_folder_path'),
    ]

    operations = [
        migrations.RenameField(
            model_name='slide',
            old_name='Folder_Id',
            new_name='Folder',
        ),
        migrations.AddField(
            model_name='slide',
            name='Tag',
            field=models.CharField(blank=True, max_length=50),
        ),
    ]