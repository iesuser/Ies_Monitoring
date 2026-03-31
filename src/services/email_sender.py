import os, logging
import utils.ies_mail_sender as ies_mail_sender
from src.workers.run_shakemap import BASE_PATH_DEFAULT

MAIL_LIST_PATH = os.path.join(os.path.dirname(__file__), "mail_list")

def email_sender(event_id, parsed_data):

    email_title = f"მიწისძვრა - {event_id}"
    email_message = f'''
    ShakeMap მზად არის event: {event_id} -თვის.

    დეტალური ინფორმაცია მიწისძვრის შესახებ:\n\n
    Event ID: {event_id}
    Time: {parsed_data["time"]}
    Location: {parsed_data["latitude"]}, {parsed_data["longitude"]}
    Depth: {parsed_data["depth"]} km
    Magnitude: {parsed_data["ml"]}
    '''

    products_path = f"{BASE_PATH_DEFAULT}/{event_id}/current/products"

    # ფაილები
    attachments = [
        os.path.join(products_path, "pga.jpg"),
        os.path.join(products_path, "pgv.jpg"),
        os.path.join(products_path, "intensity.jpg"),
    ]

    # მხოლოდ არსებული ფაილები
    existing_files = [f for f in attachments if os.path.exists(f)]

    if not existing_files:
        raise FileNotFoundError(f"No attachment files found in {products_path}")

    recipients = ies_mail_sender.get_emails(MAIL_LIST_PATH)
    if not recipients:
        raise ValueError("Mail list is empty")

    ies_mail_sender.send_mail(
        recipients,
        email_title,
        email_message,
        attachments=existing_files
    )

    logging.info(f"მეილი გაიგზავნა: {event_id}")
    return {
        "recipients": recipients,
        "attachments": existing_files,
        "products_path": products_path
    }

