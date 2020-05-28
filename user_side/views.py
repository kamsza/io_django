from django.shortcuts import render

# Create your views here.
def user_main_page_view(request, *args, **kwargs):
    return render(request, "user_page/main_page.html", {})