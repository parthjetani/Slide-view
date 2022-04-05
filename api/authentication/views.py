from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST, require_http_methods

@require_http_methods(['GET', 'POST'])
def login_request(request):
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'GET':
        data = {}
        data['javascripts'] = ['auth/login.js']
        return render(request, 'auth/login.html', data)
    elif request.method == 'POST':
        data = {
            'type': 'fail',
            'message': 'Please enter username or password'
        }
        if 'username' in request.POST and 'password' in request.POST:
            username = request.POST['username'].strip()
            password = request.POST['password'].strip()
            if len(username) == 0 or len(password) == 0:
                pass
            else:
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    login(request, user)
                    data['type'] = 'success'
                else:
                    data['type'] = 'fail'
                    data['message'] = 'Wrong username or password'
        else:
            pass
        return JsonResponse(data)

@login_required
@require_GET
def logout_request(request):
    logout(request)
    return redirect('/auth/login')
    