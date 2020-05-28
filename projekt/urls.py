"""projekt URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from public_side.views import *
from user_side.views import *

urlpatterns = [
    path('', homepage_view, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('signup/', signup_view, name='signup'),
    path('user/', userbase_view, name='user'),
    path('pricing/', pricing_view, name='pricing'),
    path('about_us/', aboutus_view, name='about us'),
    path('description/', aboutproblem_view, name='problem description'),
    path('user_page/', user_main_page_view, name='user page'),
    path('admin/', admin.site.urls),
]
