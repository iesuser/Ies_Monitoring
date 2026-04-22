from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from src.config import Config

class UrlSerializer():
    url_serializer = URLSafeTimedSerializer(Config.MY_SECRET_KEY)

    def generate_token(self, data, salt):
        token = self.url_serializer.dumps(data, salt=salt)
        return token
    
    def unload_token(self, token, salt, max_age_seconds=3600):
        try:
            data = self.url_serializer.loads(token, salt=salt, max_age=max_age_seconds)
        except SignatureExpired:
            data = 'expired'
        except BadSignature:
            data = 'invalid'
        return data