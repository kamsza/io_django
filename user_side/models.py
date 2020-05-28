from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

# Create your models here.
class Service(models.Model):
    name = models.CharField(max_length=100)
    IP = models.GenericIPAddressField()

class DNS(models.Model):
    label = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    IP = models.GenericIPAddressField()