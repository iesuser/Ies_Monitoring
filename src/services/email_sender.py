import os, logging
import utils.ies_mail_sender as ies_mail_sender

BASE_PATH_DEFAULT = "/home/sysop/shakemap_profiles/default/data"
MAIL_LIST_PATH = os.path.join(os.path.dirname(__file__), "mail_list")

def email_sender(event_id, parsed_data, base_path=BASE_PATH_DEFAULT):

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

    base_path = f"/home/sysop/shakemap_profiles/default/data/{event_id}/current/products"

    # ფაილები
    attachments = [
        os.path.join(base_path, "pga.jpg"),
        os.path.join(base_path, "pgv.jpg"),
        os.path.join(base_path, "intensity.jpg"),
    ]

    # მხოლოდ არსებული ფაილები
    existing_files = [f for f in attachments if os.path.exists(f)]

    if not existing_files:
        logging.error("არცერთი attachment ვერ მოიძებნა")
        return

    ies_mail_sender.send_mail(
        MAIL_LIST_PATH,
        email_title,
        email_message,
        attachments=existing_files
    )

    logging.info(f"მეილი გაიგზავნა: {event_id}")

