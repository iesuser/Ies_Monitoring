import logging
from src.services.calc_shakemap import calc_shakemap

BASE_PATH_DEFAULT = "/home/sysop/shakemap_profiles/default/data"
logger = logging.getLogger("app.run_shakemap")

def run_shakemap_worker(parsed_data):
    event_id = parsed_data["event_id"]

    try:
        logger.info("ShakeMap worker started for: %s", event_id)
        calc_result = calc_shakemap(parsed_data)
        if calc_result.get("stdout"):
            logger.info("ShakeMap stdout for %s: %s", event_id, calc_result["stdout"])
        if calc_result.get("stderr"):
            logger.info("ShakeMap stderr for %s: %s", event_id, calc_result["stderr"])

        # email sending is temporarily disabled
        # email_result = email_sender(event_id, parsed_data)
        logger.info("ShakeMap worker finished for: %s", event_id)
        return {
            "status": "generated",
            "event_id": event_id
        }
    except Exception as e:
        logger.error("ShakeMap worker failed for %s: %s", event_id, str(e))
        raise