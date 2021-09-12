""" Logging """
import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler('logs/spotty.log', maxBytes=3000, backupCount=10)
logging.basicConfig(level=logging.INFO,format=' %(asctime)s - %(levelname)s - %(message)s',handlers=(handler,))

from spotty import Spotty
from utils.config import spotty_token

def main():
	bot = Spotty()
	bot.load_extensions()
	bot.run(spotty_token)
	logging.info("Started spotty")

if __name__ == '__main__':
	main()
