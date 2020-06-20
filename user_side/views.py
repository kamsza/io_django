import hashlib
from datetime import datetime
import time
import yaml
import psycopg2
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .models import Subscription, Responses, Response, Service, Order, DNS, Queries, VPN
from .forms import SubscriptionForm1, SubscriptionForm2, SubscriptionForm3, SubscriptionForm5, SubscriptionForm4, StatisticsForm, ChangePasswordForm


# Create your views here.
def home_page_view(request, *args, **kwargs):
    if not request.user.is_authenticated:
        return render(request, 'user_page/403.html')

    current_user = request.user
    subscriptions = Subscription.objects.filter(user_id=current_user, end_date__gte=datetime.now())
    services = {}
    for subscription in subscriptions:
        service = subscription.service
        last_response = Responses.objects.filter(service_id=service.id).order_by('-id').first()
        services[service] = last_response
    user_services = []
    for service in services:
        result = services[service]
        if result:
            returned_ip = Response.objects.filter(responses_id=result.id).order_by('-id')
             # returned_ip = ' '.join(returned_ip)
            returned_ip = ' '
            result_str = result.result
            date = result.date.strftime('%d-%m-%Y %H:%M:%S')
        else:
            returned_ip = '-'
            result_str = '-'
            date = '-'
        user_services.append({'label': service.label,
                              'web_address': service.web_address,
                              'ip': returned_ip,
                              'result': result_str,
                              'last_checked': date
                              })

    return render(request, "user_page/home.html", {'user_services': user_services})


def profile_view(request, *args, **kwargs):
    if not request.user.is_authenticated:
        return render(request, 'user_page/403.html')

    username = request.user.username

    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            return HttpResponseRedirect('/password changed/')
    else:
        form = ChangePasswordForm()

    return render(request, "user_page/profile.html", {'username': username})


def statistics_view(request, *args, **kwargs):
    if not request.user.is_authenticated:
        return render(request, 'user_page/403.html')

    current_user = request.user
    services = []

    subscriptions = Subscription.objects.filter(user_id=current_user, end_date__gte=datetime.now())
    for subscription in subscriptions:
        services.append(subscription.service)
    chosen_service = services[0].label

    if request.method == 'POST':
        if 'filter' in request.POST:
            chosen_service = request.POST.get('service_choice')
            form = StatisticsForm(current_user, request.POST)
            form.filter(chosen_service)
            return render(request, "user_page/statistics.html", {'form': form})
        else:
            form = StatisticsForm(current_user, request.POST)
            if not form.is_valid():
                print(form.errors)
    form = StatisticsForm(current_user)

    selectStats = '''select uss.label as serviceName, usd.label as dnsName, usl.country, usr.result, usr.date from user_side_responses usr
inner join user_side_service uss on usr.service_id = uss.id
inner join user_side_dns usd on usr.dns_id = usd.id
inner join user_side_vpn usv on usr.vpn_id = usv.id
inner join user_side_location usl on usv.location_id = usl.id
where uss.label like '%''' + chosen_service + "%';"
    cur = getStats(selectStats)
    data_table = []
    error_count = 0
    success_count = 0
    failure_count = 0

    for row in cur:
        data_table.append({'service_name': row[0], 'dns_name': row[1], 'vpn_country': row[2], 'result': row[3],
                          'date': row[4]})
        if row[3] == 'successful':
            success_count += 1
        elif row[3] in 'no reponse,internal failure: out of memory,internal failure: vpn_connection_failure,internal failure: process_crash':
            failure_count += 1
        else:
            error_count += 1

    return render(request, "user_page/statistics.html", {'form': form, 'data_table': data_table,
                                                         'success_count': success_count, 'failure_count': failure_count,
                                                         'error_count': error_count})


def buy_subscription_view(request, *args, **kwargs):
    if not request.user.is_authenticated:
        return render(request, 'user_page/403.html')
    return render(request, "user_page/buy_subscription.html", {})


def error_view(request, *args, **kwargs):
    return render(request, "user_page/403.html", {})


def buy_subscription_form_1_view(request, *args, **kwargs):
    if not request.user.is_authenticated:
        return render(request, 'user_page/403.html')

    if request.method == 'POST':
        form = SubscriptionForm1(request.POST)
        if form.is_valid():
            request.session['label'] = form.data['label']
            request.session['web_address'] = form.data['web_address']
            request.session['ip'] = form.data['ip']
            return redirect('buy subscription form 2')
        else:
            return render(request, "user_page/buy_subscription_form_1.html", {'form': form})

    form = SubscriptionForm1()
    return render(request, "user_page/buy_subscription_form_1.html", {'form': form})


def buy_subscription_form_2_view(request, *args, **kwargs):
    if not request.user.is_authenticated:
        return render(request, 'user_page/403.html')

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
        elif 'clear' in request.POST:
            form = SubscriptionForm2(request.POST)
            form.clear()
            return render(request, "user_page/buy_subscription_form_2.html", {'form': form})
        else:
            form = SubscriptionForm2(request.POST)
            if form.is_valid():
                request.session['dnses'] = form.cleaned_data['multiple_checkboxes']
                request.session['user_dnses'] = list(form.user_dns_set)
                form.clear()
                return redirect('buy subscription form 3')
            else:
                return render(request, "user_page/buy_subscription_form_2.html", {'form': form, 'err': True})

    form = SubscriptionForm2()
    return render(request, "user_page/buy_subscription_form_2.html", {'form': form})


def buy_subscription_form_3_view(request, *args, **kwargs):
    if not request.user.is_authenticated:
        return render(request, 'user_page/403.html')

    if request.method == 'POST':
        if 'add' in request.POST:
            form = SubscriptionForm3(request.POST, request.FILES)
            if form.is_valid():
                f = form.cleaned_data.get('vpn_file')
                f.open(mode='rb')
                lines = f.readlines()
                config = ''.join(elem.decode("utf-8") for elem in lines)
                form.add_vpn_config(str(f), config)
                f.close()
                return render(request, "user_page/buy_subscription_form_3.html", {'form': form})
            else:
                return render(request, "user_page/buy_subscription_form_3.html", {'form': form, 'err': True})
        if 'clear' in request.POST:
            form = SubscriptionForm3(request.POST)
            form.clear()
            return render(request, "user_page/buy_subscription_form_2.html", {'form': form})
        else:
            form = SubscriptionForm3(request.POST)
            if form.is_valid():
                request.session['vpns'] = form.cleaned_data['multiple_checkboxes']
                request.session['user_vpns'] = form.user_vpns
                form.clear()
                return redirect('buy subscription form 4')
            else:
                return render(request, "user_page/buy_subscription_form_3.html", {'form': form})

    form = SubscriptionForm3()
    return render(request, "user_page/buy_subscription_form_3.html", {'form': form})


def buy_subscription_form_4_view(request, *args, **kwargs):
    if not request.user.is_authenticated:
        return render(request, 'user_page/403.html')

    if request.method == 'POST':
        form = SubscriptionForm4(request.POST)
        if 'add' in request.POST:
            email = request.POST.get('user_email')
            user = User.objects.filter(email=email)
            if user:
                if email != '':
                    form.add_user(email, user.first().id)
        else:
            request.session['users'] = list(form.users_dict.values())
            form.clear()
            return redirect('buy subscription form 5')

    form = SubscriptionForm4()
    return render(request, "user_page/buy_subscription_form_4.html", {'form': form})


def buy_subscription_form_5_view(request, *args, **kwargs):
    if not request.user.is_authenticated:
        return render(request, 'user_page/403.html')

    if request.method == 'POST':
        form = SubscriptionForm5(request.POST)
        if 'pay' in request.POST:
            form.payment_nr.append('')
            request.session['payment_id'] = ''
            return render(request, "user_page/buy_subscription_form_5.html", {'form': form, 'action': 'payed'})
        else:
            if form.payment_nr:
                label = request.session['label']
                web_address = request.session['web_address']
                ip = request.session['ip']
                dnses = request.session['dnses']
                user_dnses = request.session['user_dnses']
                vpns = request.session['vpns']
                user_vpns = request.session['user_vpns']
                users = request.session['users']
                payment_id = request.session['payment_id']
                service = create_service(label, web_address, ip)
                sub = create_subscriptions(request.user, users, service)
                create_order(sub, payment_id)
                usr_dnses = create_dns(user_dnses)
                dnses = dnses + usr_dnses
                usr_vpns = create_vpn(user_vpns)
                vpns = vpns + usr_vpns
                create_queries(service, dnses, vpns)
                form.clear()
                return redirect('user page')
            else:
                return render(request, "user_page/buy_subscription_form_5.html", {'form': form, 'action': 'not_payed'})

    form = SubscriptionForm5()
    return render(request, "user_page/buy_subscription_form_5.html", {'form': form})

def create_service(label, web_address, ip):
    service = Service(label=label, web_address=web_address, IP=ip)
    service.save()
    return service

def create_order(subscription, payment_id):
    order = Order(subscription=subscription, date=datetime.now(), value=0, payment_id=payment_id)
    order.save()

def create_subscriptions(curr_user, users_ids, service):
    sub = Subscription(user=curr_user, service=service, start_date=datetime.now(), end_date=datetime.fromtimestamp(1608137809))
    sub.save()
    for user_id in users_ids:
        x_sub = Subscription(user_id=user_id, service=service, start_date=datetime.now(), end_date=datetime.fromtimestamp(1608137809))
        x_sub.save()
    return sub

def create_dns(user_dnses_ips):
    dnses = []
    for ip in user_dnses_ips:
        x_dns = DNS(IP=ip, public=False)
        x_dns.save()
        dnses.append(x_dns.id)
    return dnses

def create_vpn(user_vpns_confs):
    vpns = []
    for config in user_vpns_confs:
        hash = hashlib.sha256(config.encode('utf-8')).hexdigest()
        x_vpn = VPN(ovpn_config=config, ovpn_config_sha256=hash, public=False)
        vpns.append(x_vpn.id)
    return vpns

def create_queries(service, dnses, vpns):
    for dns in dnses:
        for vpn in vpns:
            Queries(service=service, dns_id=dns, vpn_id=vpn, validity=1000).save()

def getStats(selectStats):
    # config = yaml.safe_load(open("db_connection_config.yml", 'r'))

    connection = psycopg2.connect(user='postgres', password='dobre haslo jest dlugie latwe do zapamietania i nieupublicznione na githubie',
                                  host='185.243.53.245', port='5432', database='ztdns')
    cursor = connection.cursor()
    cursor.execute(selectStats)
    return cursor.fetchall()
