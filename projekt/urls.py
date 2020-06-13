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
import public_side.views as public_side
import user_side.views as user_side

urlpatterns = [
    path('', public_side.homepage_view, name='home'),
    path('login/', public_side.login_view, name='login'),
    path('logout/', public_side.logout_view, name='logout'),
    path('signup/', public_side.signup_view, name='signup'),
    path('user/', public_side.userbase_view, name='user'),
    path('pricing/', public_side.pricing_view, name='pricing'),
    path('about_us/', public_side.aboutus_view, name='about us'),
    path('description/', public_side.aboutproblem_view, name='problem description'),

    path('user_page/', user_side.home_page_view, name='user page'),
    path('user_page/profile/', user_side.profile_view, name='user profile'),
    path('user_page/statistics/', user_side.statistics_view, name='user statistics'),
    path('user_page/buy/', user_side.buy_subscription_view, name='buy subscription'),
    path('user_page/buy_form/', user_side.buy_subscription_form_view, name='buy subscription form'),

    path('403/', user_side.error_view, name='error'),

    path('admin/', admin.site.urls),
]
