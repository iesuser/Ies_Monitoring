from app.extensions import api
from app.api.auth import (
    RegistrationApi,
    AuthorizationApi,
    AccessTokenRefreshApi,
    LogoutApi,
    LogoutAllApi,
)

from app.api.auth import RegistrationApi, AuthorizationApi, AccessTokenRefreshApi, LogoutApi
from app.api.accounts import CurrentUserApi, AccountsApi, AccountDetailApi