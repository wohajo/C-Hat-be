import multiprocessing
from dotenv import load_dotenv
import os

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

workers = multiprocessing.cpu_count() * 2 + 1
bind = '127.0.0.1:' + os.environ['APP_PORT']
umask = 0o007
reload = True

# logging
accesslog = '-'
errorlog = '-'
