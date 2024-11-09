from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from django.template import Context, loader


# Create your views here.

def index(request):
    if request.method=='POST':
        return render(request, 'fuzz/index.html')
    
    return render(request,'fuzz/index.html')

def test(request):

    template = loader.get_template("fuzz/unauthorized.html")
    return HttpResponse(template.render(), status=401)

def hello(request):
    template = loader.get_template("fuzz/permanent.html")
    return HttpResponse(template.render(), status=301)

def another(request):
    template = loader.get_template("fuzz/forbidden.html")
    return HttpResponse(template.render(), status=403)

