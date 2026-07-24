import os
from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
import smtplib
import logging

from app.config import Config

logger = logging.getLogger("app.mail")

class Mail:
    email_address=Config.MAIL_USERNAME
    email_password=Config.MAIL_PASSWORD
    host=Config.MAIL_SERVER
    port=Config.MAIL_PORT

    # ელფოსტის გასაგზავნი ფუნქცია
    # emails პარამეტრი შეიძლება იყოს ელფოსტის მისამართი ან ელფოსტების list ები
    # subject პარამეტრი არის ელფოსტის სათაური
    # message პარამეტრი არის ელფოსტის ტექსტი
    # email_type პარამეტრი არის ელფოსტის ტიპი (plain ან html)
    # attachments პარამეტრი შეიძლება იყოს ფაილის მისამართი ან ფაილების list ები
    # თუ attachments პარამეტრი გამოიყენება, ფაილები გამოიყენება როგორც მიმაგრებული ფაილები
    def send_mail(self, emails, subject, message, email_type='plain', attachments=None):
        try:
            # ერთი მისამართის გადმოცემისასაც list-ად გადავიყვანოთ.
            recipients = [emails] if isinstance(emails, str) else list(emails or [])
            if not recipients:
                logger.warning("Send mail skipped: recipients list is empty")
                return False

            # attachments შეიძლება იყოს ერთი path ან paths list.
            attachment_paths = []
            if attachments:
                attachment_paths = [attachments] if isinstance(attachments, str) else list(attachments)

            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = ','.join(map(str, recipients))
            msg['Subject'] = subject
            msg.attach(MIMEText(message, email_type))
            if attachment_paths:
                for file_path in attachment_paths:
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as f:
                            attachment = MIMEBase('application', 'octet-stream')
                            attachment.set_payload(f.read())
                        encoders.encode_base64(attachment)
                        attachment.add_header('Content-Disposition', f'attachment; filename={os.path.basename(file_path)}')
                        msg.attach(attachment)
                    else:
                        logger.warning("Attachment file not found: %s", file_path)
            
            # მყარდება სერვერთან კავშირი
            server = smtplib.SMTP(host=self.host, port=self.port)
        
            server.ehlo()
            server.starttls()    
            # server.ehlo()
            server.login(self.email_address, self.email_password)
            server.sendmail(self.email_address, recipients, msg.as_string())
            del msg
            # წყდება შერვერთან კავშირი
            server.quit()
            return True
        except Exception as exc:
            logger.exception("Send mail failed: %s", exc)
            return False