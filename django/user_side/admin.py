from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(Service)
admin.site.register(DNS)
admin.site.register(Location)
admin.site.register(Queries)
admin.site.register(Responses)
admin.site.register(Response)
admin.site.register(Subscription)
admin.site.register(Order)
admin.site.register(VPN)