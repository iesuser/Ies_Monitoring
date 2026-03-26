import os, logging
import utils.ies_mail_sender as ies_mail_sender

BASE_PATH_DEFAULT = "/home/sysop/shakemap_profiles/default/data"
MAIL_LIST_PATH = os.path.join(os.path.dirname(__file__), "mail_list")

def email_sender(event_id, parsed_data, base_path=BASE_PATH_DEFAULT):
    
    email_title = f"მიწისძვრა - {event_id}"
    email_message = f"""
        ShakeMap მზად არის event: {event_id} შესამოწმებლად

        Event ID: {event_id}
        Time: {parsed_data['time']}
        Location: {parsed_data['latitude']}, {parsed_data['longitude']}
        Depth: {parsed_data['depth_km']} km
        Magnitude: {parsed_data['magnitude']}
    """
    product_path = os.path.join(base_path, event_id, "current/products")
    attachments = [os.path.join(product_path, f) for f in ["pga.jpg", "pgv.jpg", "intensity.jpg"] if os.path.exists(os.path.join(product_path, f))]
    if attachments:
        ies_mail_sender.send_mail(MAIL_LIST_PATH, email_title, email_message, attachments)
        logging.info(f"Email sent for {event_id}")


