from dotenv import load_dotenv

from core import Toolkit

load_dotenv(".env")

if __name__ == "__main__":
    bot = Toolkit()
    bot.run()
