from django import forms
from .models import DNS, Location
import concurrent.futures

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
    def __init__(self, *args, **kwargs):
        super(SubscriptionForm2, self).__init__()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            ex1 = executor.submit(get_location, kwargs)
            ex2 = executor.submit(get_dnses, kwargs)
            continent_list, country_list = ex1.result()
            dns_checklist = ex2.result()
        self.fields['continent_choice'].widget = forms.Select(choices=continent_list, attrs={'class': 'custom-select d-block w-100', 'id': 'dns_continent'})
        self.fields['country_choice'].widget = forms.Select(choices=country_list, attrs={'class': 'custom-select d-block w-100', 'id': 'dns_continent'})
        self.fields['multiple_checkboxes'].widget = forms.CheckboxSelectMultiple(choices=dns_checklist)

    title = '{:^45.45} {:^15.15} {:^15.15} {:^15.15}'.format('DNS', 'IP', 'CONTINENT', 'COUNTRY')
    continent_choice = forms.ChoiceField()
    country_choice = forms.ChoiceField()
    multiple_checkboxes = forms.MultipleChoiceField()

def get_location(kwargs):
    continent_set = set()
    country_set = set()
    for location in Location.objects.all():
        if DNS.objects.filter(location=location).count():
            continent_set.add(location.continent)
            country_set.add(location.country)
    all_continents_list = [(c, c) for c in sorted(continent_set)]
    all_countries_list = [(c, c) for c in sorted(country_set)]

    if 'country' in kwargs and kwargs.get('country') is not None and kwargs.get('country')  != 'All':
        chosen_country = kwargs.get('country')
        continent = Location.objects.filter(country=chosen_country).first().continent
        country_list = [(chosen_country, chosen_country)] + [('All', ''), ('All', 'All')] + all_countries_list
        continent_list = [(continent, continent)] + [('All', ''), ('All', 'All')] + all_continents_list
    elif 'continent' in kwargs and kwargs.get('continent') is not None and kwargs.get('continent')  != 'All':
        chosen_continent = kwargs.get('continent')
        location_list = Location.objects.filter(continent=chosen_continent)
        country_set = set()
        for location in location_list:
            country_set.add(location.country)
        country_list = [('All', 'All')] + [(c, c) for c in sorted(country_set)] + [('All', ''), ('All', 'All')] + all_countries_list
        continent_list = [(chosen_continent, chosen_continent)] + [('All', ''), ('All', 'All')] + all_continents_list
    else:
        country_list =[('All', 'All')] + all_countries_list
        continent_list =[('All', 'All')] + all_continents_list

    return continent_list, country_list

def get_dnses(kwargs):
    if 'country' in kwargs and kwargs.get('country') is not None and kwargs.get('country')  != 'All':
        country = kwargs.get('country')
        dns_list = DNS.objects.filter(location__country=country).order_by('location__continent', 'location__country', 'label', 'IP')
    elif 'continent' in kwargs and kwargs.get('continent') is not None and kwargs.get('continent') != 'All':
        continent = kwargs.get('continent')
        dns_list = DNS.objects.filter(location__continent=continent).order_by('location__continent', 'location__country', 'label', 'IP')
    else:
        dns_list = DNS.objects.order_by('location__continent', 'location__country', 'label', 'IP')

    dns_checklist = []
    for dns in dns_list:
        label = '{:45.43} {:15.15} {:15.12} {:15.12}'.format(dns.label, dns.IP, dns.location.continent, dns.location.country)
        dns_checklist.append((dns, label))
    return dns_checklist
