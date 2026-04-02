from src.config import Config
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import smtplib

class Mail:
    email_address=Config.MAIL_USERNAME
    email_password=Config.MAIL_PASSWORD
    host=Config.MAIL_SERVER
    port=Config.MAIL_PORT

    def send_mail(self,emails, subject, message, email_type='plain'):
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = ','.join(map(str, emails))
            msg['Subject'] = subject
            msg.attach(MIMEText(message, email_type))
            
            # მყარდება სერვერთან კავშირი
            server = smtplib.SMTP(host=self.host, port=self.port)
        
            server.ehlo()
            server.starttls()    
            # server.ehlo()
            server.login(self.email_address, self.email_password)
            server.sendmail("", emails, msg.as_string())
            del msg
            # წყდება შერვერთან კავშირი
            server.quit()
            return True
        except:
            return False