from django import forms


class SubscriptionForm(forms.Form):
    label = forms.CharField(max_length=40,
                            widget=forms.TextInput(
                                attrs={'class': 'form-control', 'placeholder': 'How do you want to call service ... (optional)', 'id': 'label'}))

    web_address = forms.URLField(required=True,
                                 widget=forms.TextInput(
                                     attrs={'class': 'form-control', 'placeholder': 'Valid URL e.g. www.my_service.com', 'id': 'url'}))

    ip = forms.GenericIPAddressField(max_length=15,
                                     required=True,
                                     widget=forms.TextInput(
                                         attrs={'class': 'form-control', 'placeholder': 'Correct IP of your service', 'id': 'ip'}))
