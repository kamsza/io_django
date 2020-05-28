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

class Location(models.Model):
    dns = models.ForeignKey('DNS', on_delete=models.CASCADE, related_name='+')
    continent = models.CharField(max_length=20)
    country = models.CharField(max_length=20)
    address = models.CharField(max_length=50, null=True)
    
class Service_DNS(models.Model):
    service = models.ForeignKey('Service', on_delete=models.SET_NULL)
    dns = models.ForeignKey('DNS', on_delete=models.SET_NULL, null=True)

class History(models.Model):
    service = models.ForeignKey('Service', on_delete=models.CASCADE)
    dns = models.ForeignKey('DNS', on_delete=models.SET_NULL, null=True)
    date = models.DateTimeField(default=timezone.now)
    result = models.CharField(max_length=50)
    
class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    service = models.ForeignKey('Service', on_delete=models.SET_NULL)
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField()
    
class Order(models.Model):
    subscription = models.ForeignKey('Subscription', on_delete=models.DO_NOTHING)
    date = models.DateField(auto_now_add=True)
    value = models.DecimalField(max_digits=6, decimal_places=2)
    payment_id = models.CharField(max_length=20)