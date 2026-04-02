from src.api.nsmodels.seismic_event import event_ns, event_parser, event_model
from src.api.nsmodels.calc_shakemap import shakemap_ns, shakemap_parser, shakemap_model
from src.api.nsmodels.auth import auth_ns, registration_parser, auth_parser
from src.api.nsmodels.accounts import accounts_ns, user_model, user_parser, accounts_model, accounts_parser, roles_model, roles_parser, password_reset_parser, request_password_reset_parser, change_password_parser