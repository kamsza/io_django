from django import forms
from .models import DNS, VPN, Location, Subscription
import concurrent.futures


class ChangePasswordForm(forms.Form):
    password1 = forms.CharField(label='new password', max_length=25)
    password2 = forms.CharField(label='confirm new password', max_length=25)


class StatisticsForm(forms.Form):
    service_choice = forms.ChoiceField(required=False, widget=forms.Select(attrs={'class': 'custom-select d-block w-100', 'id': 'service_label'}))

    def __init__(self, user, *args, **kwargs):
        super(StatisticsForm, self).__init__(*args, **kwargs)
        self.user = user
        service_list = Subscription.objects.filter(user_id=self.user).order_by('service__label')
        service_list = [(subscription.service.label, subscription.service.label) for subscription in service_list]
        self.user_services_list = service_list
        self.fields['service_choice'].choices = self.user_services_list

    def filter(self, label):
        service_list = Subscription.objects.filter(user_id=self.user).order_by('service__label')
        service_list = [(subscription.service.label, subscription.service.label) for subscription in service_list]
        if (label, label) in service_list:
            service_list.remove((label, label))
            service_list = [(label, label)] + service_list
        self.user_services_list = service_list
        self.fields['service_choice'].choices = self.user_services_list


class SubscriptionForm1(forms.Form):
    label = forms.CharField(max_length=40,
                            required=False,
                            widget=forms.TextInput(
                                attrs={'class': 'form-control', 'placeholder': 'How do you want to call service ... (optional)', 'id': 'label'}))

    web_address = forms.URLField(required=True,
                                 widget=forms.TextInput(
                                     attrs={'class': 'form-control', 'placeholder': 'Valid URL e.g. www.my_service.com', 'id': 'url'}))

    ip = forms.GenericIPAddressField(max_length=15,
                                     required=True,
                                     widget=forms.TextInput(
                                         attrs={'class': 'form-control', 'placeholder': 'Correct IP of your service', 'id': 'ip'}))


class SubscriptionForm2(forms.Form):
    title = '{:^45.45} {:^15.15} {:^15.15} {:^15.15}'.format('DNS', 'IP', 'CONTINENT', 'COUNTRY')
    user_dns_set = set()
    continent_choice = forms.ChoiceField(required=False, widget=forms.Select(attrs={'class': 'custom-select d-block w-100', 'id': 'dns_continent'}))
    country_choice = forms.ChoiceField(required=False, widget=forms.Select(attrs={'class': 'custom-select d-block w-100', 'id': 'dns_continent'}))
    multiple_checkboxes = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple())
    user_dns_ip = forms.GenericIPAddressField(max_length=15,
                                              required=False,
                                              widget=forms.TextInput(
                                                  attrs={'class': 'form-control', 'placeholder': 'Correct IP of DNS', 'id': 'dns_ip'}))

    def __init__(self, *args, **kwargs):
        super(SubscriptionForm2, self).__init__(*args, **kwargs)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            ex1 = executor.submit(get_location_dns, None, None)
            ex2 = executor.submit(get_dnses, None, None)
            self.continent_list, self.country_list = ex1.result()
            self.dns_checklist = ex2.result()
        self.fields['continent_choice'].choices = self.continent_list
        self.fields['country_choice'].choices = self.country_list
        self.fields['multiple_checkboxes'].choices = self.dns_checklist

    def add_user_dns(self, ip):
        self.user_dns_set.add(ip)

    def filter(self, continent, country):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            ex1 = executor.submit(get_location_dns, continent, country)
            ex2 = executor.submit(get_dnses, continent, country)
            self.continent_list, self.country_list = ex1.result()
            self.dns_checklist = ex2.result()
        self.fields['continent_choice'].choices = self.continent_list
        self.fields['country_choice'].choices = self.country_list
        self.fields['multiple_checkboxes'].choices = self.dns_checklist

    def clear(self):
        self.user_dns_set.clear()

class SubscriptionForm3(forms.Form):
    title = '{:30.25} {:30.25}'.format('CONTINENT', 'COUNTRY')
    vpn_checklist = []
    file_names = []
    user_vpns = []
    for vpn in VPN.objects.filter(public=True).order_by('location__continent', 'location__country'):
        label = '{:30.25} {:30.25}'.format(vpn.location.continent, vpn.location.country)
        vpn_checklist.append((vpn.id, label))
    multiple_checkboxes = forms.MultipleChoiceField(choices=vpn_checklist, required=False, widget=forms.CheckboxSelectMultiple())
    vpn_file = forms.FileField(required=False)

    def add_vpn_config(self, file_name, config):
        if file_name not in self.file_names:
            self.file_names.append(file_name)
            self.user_vpns.append(config)

    def clear(self):
        self.vpn_checklist.clear()
        self.file_names.clear()
        self.user_vpns.clear()


class SubscriptionForm4(forms.Form):
    user_email = forms.EmailField(required=False,
                                  widget=forms.TextInput(
                                      attrs={'class': 'form-control', 'placeholder': 'User email', 'id': 'user_email', 'name': 'user_email'}))
    users_dict = {}

    def add_user(self, email, user):
        self.users_dict[email] = user

    def clear(self):
        self.users_dict.clear()


class SubscriptionForm5(forms.Form):
    payment_nr = []

    def add_payment_id(self, _id):
        self.payment_nr.append(_id)

    def clear(self):
        self.payment_nr.clear()


def get_location_dns(continent, country):
    continent_set = set()
    country_set = set()
    for location in Location.objects.all():
        if DNS.objects.filter(location=location, public=True).count():
            continent_set.add(location.continent)
            country_set.add(location.country)
    all_continents_list = [(c, c) for c in sorted(continent_set)]
    all_countries_list = [(c, c) for c in sorted(country_set)]

    if country is not None and country != 'All':
        continent = Location.objects.filter(country=country).first().continent
        country_list = [(country, country)] + [('All', ''), ('All', 'All')] + all_countries_list
        continent_list = [(continent, continent)] + [('All', ''), ('All', 'All')] + all_continents_list
    elif continent is not None and continent != 'All':
        location_list = Location.objects.filter(continent=continent)
        country_set = set()
        for location in location_list:
            country_set.add(location.country)
        country_list = [('All', 'All')] + [(c, c) for c in sorted(country_set)] + [('All', ''), ('All', 'All')] + all_countries_list
        continent_list = [(continent, continent)] + [('All', ''), ('All', 'All')] + all_continents_list
    else:
        country_list = [('All', 'All')] + all_countries_list
        continent_list = [('All', 'All')] + all_continents_list
    return continent_list, country_list


def get_dnses(continent, country):
    if country is not None and country != 'All':
        dns_list = DNS.objects.filter(location__country=country, public=True).order_by('location__continent', 'location__country', 'label', 'IP')
    elif continent is not None and continent != 'All':
        dns_list = DNS.objects.filter(location__continent=continent, public=True).order_by('location__continent', 'location__country', 'label', 'IP')
    else:
        dns_list = DNS.objects.filter(public=True).order_by('location__continent', 'location__country', 'label', 'IP')
    dns_checklist = []
    for dns in dns_list:
        label = '{:45.43} {:15.15} {:15.12} {:15.12}'.format(dns.label, dns.IP, dns.location.continent, dns.location.country)
        dns_checklist.append((dns.id, label))
    return dns_checklist


def get_user_services(label, user):
    if label is not None:
        user_subscription_list = Subscription.objects.filter(service__label=label, user_id=user).order_by('service__label')
    else:
        user_subscription_list = Subscription.objects.filter(user_id=user).order_by('service__label')
    result = [(subscription.service.label, subscription.service.label) for subscription in user_subscription_list]
    return result
