import os
import asyncio

from telegram import Bot
from dotenv import load_dotenv

from database import database

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')


class WebhookService:
    def __init__(self):
        # Mapping string names to method references
        self.commands = {
            "get_funding_data_file": self.get_funding_data_file,
            "get_24hr_volume": self.get_24hr_volume,
            "download_growth": self.download_growth
        }

        self.bot = Bot(TELEGRAM_BOT_TOKEN)


    async def get_funding_data_file(self, user_id: int, telegram_id: int, *args, **kwargs):
        csv_file_path = f"../dataframes/funding_data_{user_id}.csv"

        try:
            with open(csv_file_path, 'rb') as file:
                await self.bot.send_document(chat_id=telegram_id, document=file, filename="funding_data.csv")
        except FileNotFoundError:
            return "no_file"

        return {"Status": "ok"}


    async def get_24hr_volume(self, csv_file_path: str, telegram_id: int, *args, **kwargs):
        file_name = csv_file_path.split("/")[-1]
        with open(csv_file_path, 'rb') as file:
            await self.bot.send_document(chat_id=telegram_id, document=file, filename=file_name)

        return {"Status": "ok"}


    async def download_growth(self, csv_file_path: str, telegram_id: int, *args, **kwargs):
        if not csv_file_path:
            return "no_file_path"

        try:
            with open(csv_file_path, 'rb') as file:
                await self.bot.send_document(chat_id=telegram_id, document=file, filename="growth_data.csv")
        except FileNotFoundError:
            return "no_file"

        return {"Status": "ok"}


    async def execute_command(self, command_name, *args, **kwargs):
        if command_name in self.commands:
            command = self.commands[command_name]
            if asyncio.iscoroutinefunction(command):
                print(f"Executing async command: {command_name}")
                result = await command(*args, **kwargs)
                print(f"Async command {command_name} completed with result: {result}")
                return result
            else:
                print(f"Executing sync command: {command_name}")
                result = command(*args, **kwargs)
                print(f"Sync command {command_name} completed with result: {result}")
                return result
        else:
            raise ValueError(f"Command '{command_name}' not found")


service = WebhookService()


# Dynamically call functions by name
# asyncio.run(service.execute_command("download_growth", "asdfasdf", 'asdfasdf'))
# service.execute_command("process_data", {"name": "test", "value": 42})
# service.execute_command("handle_error", 404, "Page not found")
