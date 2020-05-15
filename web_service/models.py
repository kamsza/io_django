from django.db import models

# Create your models here.
class WebService(models.Model):
    name = models.TextField()
    url  = models.TextField()
