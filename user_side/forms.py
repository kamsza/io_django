from django import forms
from .models import DNS, Location


class SubscriptionForm(forms.Form):
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
    dns_checklist = []
    for dns in DNS.objects.order_by('location__continent', 'location__country', 'label', 'IP'):
        label = '{:45.43} {:15.15} {:15.12} {:15.12}'.format(dns.label, dns.IP, dns.location.continent, dns.location.country)
        dns_checklist.append((dns, label))

    continent_set = set()
    country_set = set()
    for location in Location.objects.all():
        if DNS.objects.filter(location=location).count():
            continent_set.add(location.continent)
            country_set.add(location.country)
    continent_list = [(c, c) for c in sorted(continent_set)]
    continent_list = [('All', 'All')] + continent_list
    country_list = [(c, c) for c in sorted(country_set)]
    country_list = [('All', 'All')] + country_list

    title = '{:^45.45} {:^15.15} {:^15.15} {:^15.15}'.format('DNS', 'IP', 'CONTINENT', 'COUNTRY')
    continent_choice = forms.ChoiceField(choices=continent_list,
                                         widget=forms.Select(
                                             attrs={'class': 'custom-select d-block w-100', 'id': 'dns_continent'}
                                         ))
    country_choice = forms.ChoiceField(choices=country_list,
                                       widget=forms.Select(
                                           attrs={'class': 'custom-select d-block w-100', 'id': 'dns_continent'}
                                       ))
    multiple_checkboxes = forms.MultipleChoiceField(choices=dns_checklist, widget=forms.CheckboxSelectMultiple)
