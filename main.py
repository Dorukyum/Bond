from os import environ
from dotenv import load_dotenv
from utils import PycordManager

bot = PycordManager()
load_dotenv(".env")
bot.run(environ.get("TOKEN"))
