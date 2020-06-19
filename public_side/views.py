from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from public_side.models import CreateUserForm

# HOME PAGE
def homepage_view(request, *args, **kwargs):
    return render(request, "home_page/home_page.html", {})

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
            user = form.cleaned_data.get('username')
            messages.success(request, 'Account for ' + user + ' created.')
            return redirect('login')

    context = {'form': form}
    return render(request, "home_page/sign_up.html", context)

def login_view(request, *args, **kwargs):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('user page')
        else:
            messages.info(request, 'Username or password is incorrect')

    context = {}
    return render(request, "home_page/log_in.html", context)

def logout_view(request):
    logout(request)
    return redirect('home')
