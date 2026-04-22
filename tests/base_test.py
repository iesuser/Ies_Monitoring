import unittest

from src import create_app
from src.config import TestConfig
from src.extensions import db


class BaseTestCase(unittest.TestCase):
    """უნიტესტების ბაზური კლასი TestConfig-ით."""

    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
