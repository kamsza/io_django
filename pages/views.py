from django.shortcuts import render
from django.http import HttpResponse


# Create your views here.
def homepage_view(request, *args, **kwargs):
    return render(request, "home_page/home_page.html", {})

def login_view(request, *args, **kwargs):
    return render(request, "home_page/log_in.html", {})

def signup_view(request, *args, **kwargs):
    return render(request, "home_page/sign_up.html", {})

def userbase_view(request, *args, **kwargs):
    return render(request, "user_page_base.html", {})