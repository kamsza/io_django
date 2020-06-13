from django import forms

class SubscriptionForm(forms.Form):
    label = forms.CharField()