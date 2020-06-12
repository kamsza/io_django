from datetime import datetime

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from .models import Subscription, Responses, Response

user_dns_list = [
    {
        'label': 'Service 1',
        'name': 'www.service1.pl',
        'status': 'OK',
        'last_checked': '1.06.2020 r. 18:23'
    },
    {
        'label': 'Service 1',
        'name': 'www.service2.pl',
        'status': 'WRONG IP',
        'last_checked': '1.06.2020 r. 18:36'
    },
    {
        'label': 'Service 3',
        'name': 'www.service3.pl',
        'status': 'OK',
        'last_checked': '2.06.2020 r. 17:08'
    },
    {
        'label': 'Service 4',
        'name': 'www.service4.pl',
        'status': 'OK',
        'last_checked': '2.06.2020 r. 19:52'
    }
]

# Create your views here.
def home_page_view(request, *args, **kwargs):
    context = {
        'user_dns_list': user_dns_list
    }
    if not request.user.is_authenticated:
        return render(request, 'user_page/403.html')

    current_user = request.user
    subscriptions = Subscription.objects.filter(user_id=current_user, end_date__gte=datetime.now())
    services = []
    for subscription in subscriptions:
        services.append(subscription.service)
    responses = []
    for service in services:
        last_response = Responses.objects.filter(service_id=service.id).order_by('-id').first()
        if last_response:
            responses.append(last_response)
    user_services = []
    for registry in responses:
        returned_ip = Response.objects.filter(responses_id=registry.id).order_by('-id').first()
        user_services.append({'label': registry.service.name,
                              'ip': returned_ip,
                              'status': registry.result,
                              'last_checked': registry.date
                              })

    return render(request, "user_page/home.html", {'user_services': {}})


def profile_view(request, *args, **kwargs):
    if not request.user.is_authenticated:
        return render(request, 'user_page/403.html')
    return render(request, "user_page/profile.html", {})

def statistics_view(request, *args, **kwargs):
    if not request.user.is_authenticated:
        return render(request, 'user_page/403.html')
    return render(request, "user_page/statistics.html", {})

def buy_subscription_view(request, *args, **kwargs):
    if not request.user.is_authenticated:
        return render(request, 'user_page/403.html')
    return render(request, "user_page/buy_subscription.html", {})

def error_view(request, *args, **kwargs):
    return render(request, "user_page/403.html", {})
