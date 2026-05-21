from django.shortcuts import render

def dashboard(request):
    return render(request, 'main/dashboard.html')

def login_view(request):
    return render(request, 'main/login.html')

def logout_view(request):
    pass

def register_view(request):
    return render(request, 'main/register.html')