from dotenv import load_dotenv

from core import PycordManager

load_dotenv(".env")

if __name__ == "__main__":
    bot = PycordManager()
    bot.run()
