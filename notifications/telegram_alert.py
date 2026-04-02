import asyncio
from telegram import Bot
from telegram.request import HTTPXRequest
# Import your config (ensure settings.py has these variables)
from config.settings import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

class TelegramNotify:
    def __init__(self):
        # Using a longer timeout to prevent the 'Timed Out' error we saw earlier
        self.request_obj = HTTPXRequest(connect_timeout=20, read_timeout=20)
        self.bot = Bot(token=TELEGRAM_TOKEN, request=self.request_obj)
        self.chat_id = TELEGRAM_CHAT_ID

    async def send_message(self, text):
        try:
            await self.bot.send_message(chat_id=self.chat_id, text=text, parse_mode='Markdown')
        except Exception as e:
            print(f"❌ Telegram Error: {e}")

    def send_sync_message(self, text):
        """Helper to send messages from main.py without managing loops"""
        try:
            # Get the current running loop or create a new one
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            if loop.is_running():
                loop.create_task(self.send_message(text))
            else:
                loop.run_until_complete(self.send_message(text))
        except Exception as e:
            print(f"❌ Telegram Sync Error: {e}")

# ========================================================
# CRITICAL: This is the line your main.py is looking for!
# ========================================================
notifier = TelegramNotify()