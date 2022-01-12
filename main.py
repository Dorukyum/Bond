from dotenv import load_dotenv
from utils import PycordManager


load_dotenv(".env")
bot = PycordManager()
bot.run()
