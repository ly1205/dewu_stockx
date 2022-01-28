import logging
import os
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s')
formatter = logging.Formatter('%(asctime)s - %(threadName)s - %(levelname)s - %(message)s')
logger = logging.getLogger()
fname = os.path.basename(sys.argv[0]).split(".")[0]
if not os.path.exists('./logs'):
    os.mkdir('./logs')
file_handler = logging.FileHandler('./logs/'+fname+'.log', mode='w', encoding='GBK')
file_handler.setLevel(level=logging.INFO)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# stream_handler = logging.StreamHandler()
# stream_handler.setLevel(logging.INFO)
# logger.addHandler(stream_handler)
