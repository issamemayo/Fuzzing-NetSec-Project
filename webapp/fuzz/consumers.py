# fuzz/consumers.py
import json
from channels.generic.websocket import WebsocketConsumer

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()  # Accept the WebSocket connection

    def disconnect(self, close_code):
        pass  # No actions on disconnect

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Echo the received message back to the client
        self.send(text_data=json.dumps({
            'message': message
        }))
