from django.shortcuts import render

user_dns_list = [
    {
        'label': 'DNS 1',
        'ip': '192.168.0.3',
        'status': 'OK',
        'last_checked': '1.06.2020 r. 18:23'
    },
    {
        'label': 'DNS 2',
        'ip': '192.168.0.4',
        'status': 'WRONG IP',
        'last_checked': '1.06.2020 r. 18:36'
    }
]

# Create your views here.
def main_page_view(request, *args, **kwargs):
    return render(request, "user_page/main_page.html", {})

def home_page_view(request, *args, **kwargs):
    context = {
        'user_dns_list': user_dns_list
    }
    return render(request, "user_page/main_page.html", context)
