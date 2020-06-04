from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from .models import Subscription, Responses, Response

user_dns_list = [
    {
        'label': 'DNS 1',
        'ip': '192.168.0.3',
        'status': 'OK',
        'last_checked': '1.06.2020 r. 18:23'
    },
    {
        'label': 'DNS 2',
        'ip': '192.168.0.4',
        'status': 'WRONG IP',
        'last_checked': '1.06.2020 r. 18:36'
    }
]

# Create your views here.
def home_page_view(request, *args, **kwargs):
    context = {
        'user_dns_list': user_dns_list
    }

    current_user = request.user
    subscriptions = Subscription.objects.filter(user_id=current_user)
    services = []
    for subscription in subscriptions:
        services.append(subscription.service)
    responses = []
    for service in services:
        responses.append(Responses.objects.filter(service_id=service.id).order_by('-id')[0])
    user_services = []
    for registry in responses:
        returned_ip = Response.objects.filter(responses_id=registry.id).order_by('-id')[0]
        user_services.append({'label': registry.service.name,
                              'ip': returned_ip,
                              'status': registry.result,
                              'last_checked': registry.date
                              })

    return render(request, "user_page/main_page.html", {'user_services': user_services})
