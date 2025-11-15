import aiomax
import asyncio
import os
from dotenv import load_dotenv
load_dotenv('keys.env')
token = os.getenv("MAX_VK_BOT_TOKEN")
if not token:
    raise RuntimeError("MAX_VK_BOT_TOKEN not found in keys.env")

bot = aiomax.Bot(token, default_format='markdown')

@bot.on_message()
async def echo(message: aiomax.Message):
    await message.reply(message.body.text)

bot.run()