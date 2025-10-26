import logging
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(filename)s:%(lineno)d - %(funcName)s() - %(levelname)s - %(message)s", 
    filename="underwriter.log", 
    filemode="a"
)
logger = logging.getLogger("underwriter") 