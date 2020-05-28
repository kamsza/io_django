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
    
class Service_DNS(models.Model):
    service = models.ForeignKey('Service', on_delete=models.SET_NULL)
    dns = models.ForeignKey('DNS', on_delete=models.SET_NULL, null=True)

class History(models.Model):
    service = models.ForeignKey('Service', on_delete=models.CASCADE)
    dns = models.ForeignKey('DNS', on_delete=models.SET_NULL, null=True)
    date = models.DateTimeField(default=timezone.now)
    result = models.CharField(max_length=50)