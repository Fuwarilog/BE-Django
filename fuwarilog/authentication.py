import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from fuwarilog.settings import JWT_KEY
from fuwarilog.ex_rates.models import User

class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        token = request.COOKIES.get('access_token')

        if not token:
            raise AuthenticationFailed('Access Token이 필요합니다.')

        try:
            payload = jwt.decode(token, JWT_KEY, algorithms=['HS256'])
        except ExpiredSignatureError:
            raise AuthenticationFailed('Access Token이 만료되었습니다.')
        except InvalidTokenError:
            raise AuthenticationFailed('Access Token이 유효하지 않습니다.')

        email = payload.get("sub")
        if not email:
            raise AuthenticationFailed('Access Token이 잘못되었습니다.')

        try:
            user = User.objects.get(email=payload["sub"])
        except User.DoesNotExist:
            raise AuthenticationFailed('사용자가 존재하지 않습니다.')

        return (user, None)