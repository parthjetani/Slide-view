# Generated by Django 3.1.6 on 2021-03-04 16:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0008_slide_tag'),
    ]

    operations = [
        migrations.AddField(
            model_name='slide',
            name='CopyOf',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='copy', to='dashboard.slide'),
        ),
    ]