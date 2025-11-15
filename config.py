import os
import dotenv
from dotenv import load_dotenv

load_dotenv("keys.env")

MAX_VK_BOT_TOKEN = os.getenv("MAX_VK_BOT_TOKEN")
RESPONSES_PATH = "data/responses.json"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
MAX_VK_BOT_USERNAME = os.getenv("MAX_VK_BOT_USERNAME")