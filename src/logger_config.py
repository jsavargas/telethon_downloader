import logging
import inspect

def LoggerConfig():
    # Get the name of the calling module
    frame = inspect.stack()[1]
    module = inspect.getmodule(frame[0])
    name = module.__name__ if module else __name__

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Create console handler and set level to info
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Add formatter to ch
    ch.setFormatter(formatter)
    
    # Add ch to logger
    if not logger.handlers: # Prevent adding multiple handlers if already exists
        logger.addHandler(ch)

    return logger