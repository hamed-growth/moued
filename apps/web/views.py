from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required(login_url='missions:home')
def dashboard(request):
    return render(request, 'missions/dashboard.html')
