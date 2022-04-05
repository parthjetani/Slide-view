from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class CustomUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    organization_id = models.CharField(max_length=15, null=True)
    organization_name = models.CharField(max_length=100, null=True)
    organization_role = models.CharField(max_length=100, null=True)
    phone_number = models.CharField(max_length=15, null=True)
    avatar = models.ImageField(default='default.jpg')
