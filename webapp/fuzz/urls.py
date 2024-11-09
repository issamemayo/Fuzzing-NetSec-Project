from django.urls import path
from . import views

app_name="fuzz"

urlpatterns=[
    path("", views.index, name="index"),
    path("test",views.test,name="test"),
    path("hello",views.hello,name="hello"), 
    path("another",views.another, name="another")

]