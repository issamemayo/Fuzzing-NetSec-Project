# fuzz/routing.py
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/fuzz/', consumers.ChatConsumer.as_asgi()),  # Make sure this matches the WebSocket URL in your JS
]
