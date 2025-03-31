from channels.generic.websocket import AsyncWebsocketConsumer
import json

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send(json.dumps({"message": "Connected to Healthra Updates"}))

    async def receive(self, text_data):
        data = json.loads(text_data)
        await self.send(json.dumps({"message": f"New update: {data['message']}"}))