from datetime import datetime

from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .models import Subscription, Responses, Response
from .forms import SubscriptionForm, SubscriptionForm2, SubscriptionForm3

user_dns_list = [
    {
        'label': 'Service 1',
        'name': 'www.service1.pl',
        'status': 'OK',
        'last_checked': datetime.fromtimestamp(1591038723).strftime('%d-%m-%Y %H:%M:%S')
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

    return render(request, "user_page/home.html", {'user_services': user_dns_list})
    # return render(request, "user_page/home.html", {'user_services': {}})


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


def buy_subscription_form_1_view(request, *args, **kwargs):
    if not request.user.is_authenticated:
        return render(request, 'user_page/403.html')

    form = SubscriptionForm()

    if request.method == 'POST':
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            print(form.data['label'])
            print(form.data['web_address'])
            print(form.data['ip'])
            return redirect('buy subscription form 2')

    return render(request, "user_page/buy_subscription_form_1.html", {'form': form})


def buy_subscription_form_2_view(request, *args, **kwargs):
    if not request.user.is_authenticated:
        return render(request, 'user_page/403.html')
    print(request.POST)
    if request.method == 'POST':
        if 'filter' in request.POST:
            continent = request.POST.get('continent_choice')
            country = request.POST.get('country_choice')
            form = SubscriptionForm2(request.POST)
            form.filter(continent, country)
            return render(request, "user_page/buy_subscription_form_2.html", {'form': form})
        elif 'add' in request.POST:
            dns_ip = request.POST.get('user_dns_ip')
            form = SubscriptionForm2(request.POST)
            form.add_user_dns(dns_ip)
            return render(request, "user_page/buy_subscription_form_2.html", {'form': form})
        else:
            form = SubscriptionForm2(request.POST)
            print(form.fields['multiple_checkboxes'])
            if form.is_valid():
                print(form.cleaned_data['multiple_checkboxes'])
                print(form.user_dns_list)
                return redirect('buy subscription form 3')
            else:
                print(form.errors)

    form = SubscriptionForm2()
    return render(request, "user_page/buy_subscription_form_2.html", {'form': form})


def buy_subscription_form_3_view(request, *args, **kwargs):
    if not request.user.is_authenticated:
        return render(request, 'user_page/403.html')

    if request.method == 'POST':
        return redirect('buy subscription')

    form = SubscriptionForm3()
    return render(request, "user_page/buy_subscription_form_3.html", {'form': form})
