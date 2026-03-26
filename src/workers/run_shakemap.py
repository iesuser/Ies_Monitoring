from threading import Thread
import logging
from src.services.calc_shakemap import calc_shakemap
from src.services.email_sender import email_sender

def run_shakemap_worker(parsed_data):
    event_id = parsed_data["event_id"]
    try:
        logging.info("ShakeMap worker started for: %s", event_id)
        calc_shakemap(parsed_data)
        email_sender(event_id, parsed_data)
        logging.info("ShakeMap worker finished for: %s", event_id)
    except Exception as e:
        logging.error("ShakeMap worker failed for %s: %s", event_id, str(e))