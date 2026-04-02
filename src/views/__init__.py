"""Views პაკეტის ექსპორტები.

ეს პაკეტი აექსპორტებს Flask blueprint-ებს,
რომლებიც HTML გვერდების რენდერზე არიან პასუხისმგებელი.
"""

from src.views.shakemap.routes import shakemap_blueprint
from src.views.auth.routes import auth_blueprint
from src.views.accounts.routes import accounts_blueprint
from src.views.events.routes import events_blueprint