from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm

from pages.forms import CreateUserForm

# HOME PAGE
def homepage_view(request, *args, **kwargs):
    return render(request, "home_page/home_page.html", {})

def login_view(request, *args, **kwargs):
    return render(request, "home_page/log_in.html", {})

def pricing_view(request, *args, **kwargs):
    return render(request, "home_page/pricing.html", {})

def aboutus_view(request, *args, **kwargs):
    return render(request, "home_page/about_us.html", {})

def aboutproblem_view(request, *args, **kwargs):
    return render(request, "home_page/problem_description.html", {})

# USER PAGE
def userbase_view(request, *args, **kwargs):
    return render(request, "user_page_base.html", {})


def signup_view(request, *args, **kwargs):
    form = CreateUserForm()

    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save()

    context = {'form': form}
    return render(request, "home_page/sign_up.html", context)