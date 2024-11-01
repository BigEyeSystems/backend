import os

from telegram import Bot
from dotenv import load_dotenv

from database import database

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')


class WebhookService:
    def __init__(self):
        # Mapping string names to method references
        self.commands = {
            "send_webhook": self.get_funding_data_file,
            "process_data": self.get_24hr_volume,
            "handle_error": self.download_growth
        }

        self.bot = Bot(TELEGRAM_BOT_TOKEN)


    async def get_funding_data_file(self, user_id: int, telegram_id: int):
        csv_file_path = f"dataframes/funding_data_{user_id}.csv"
        with open(csv_file_path, 'rb') as file:
            await self.bot.send_document(chat_id=telegram_id, document=file, filename="funding_data.csv")

        return {"Status": "ok"}


    async def get_24hr_volume(self, file_id: int, telegram_id: int):
        file_path = database.execute_with_return(
            """
            SELECT directory
            FROM data_history.volume_data_history
            WHERE file_id = $1 
            """, file_id
        )[0][0]

        csv_file_path = file_path.get("directory")
        file_name = csv_file_path.split("/")[-1]
        with open(csv_file_path, 'rb') as file:
            await self.bot.send_document(chat_id=telegram_id, document=file, filename=file_name)

        return {"Status": "ok"}


    async def download_growth(self, file_id: int, user_id: int, telegram_id: int):
        if not file_id:
            return {"Provide file id!"}

        file_params = database.execute_with_return(
            """
            SELECT *
            FROM data_history.growth_data_history
            WHERE file_id = $1 AND user_id = $2;
            """, file_id, user_id
        )

        date_param = file_params.get("date")
        time_param = file_params.get("time")
        file_name = file_params.get("file_name")

        csv_file_path = f"dataframes/{user_id}/{date_param}/{time_param}/{file_name}"

        with open(csv_file_path, 'rb') as file:
            await self.bot.send_document(chat_id=telegram_id, document=file, filename="growth_data.csv")

        return {"Status": "ok"}


    def execute_command(self, command_name, *args, **kwargs):
        if command_name in self.commands:
            return self.commands[command_name](*args, **kwargs)
        else:
            raise ValueError(f"Command '{command_name}' not found")


service = WebhookService()

# Dynamically call functions by name
# service.execute_command("send_webhook", "https://example.com", {"key": "value"})
# service.execute_command("process_data", {"name": "test", "value": 42})
# service.execute_command("handle_error", 404, "Page not found")
