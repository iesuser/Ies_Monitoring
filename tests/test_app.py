from tests.base_test import BaseTestCase


class AppConfigTests(BaseTestCase):
    def test_test_config_is_loaded(self):
        self.assertTrue(self.app.config["TESTING"])
        self.assertEqual(self.app.config["SQLALCHEMY_DATABASE_URI"], "sqlite:///:memory:")

    def test_home_route_returns_success(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)


class EventsApiTests(BaseTestCase):
    def test_events_endpoint_returns_404_when_empty(self):
        response = self.client.get("/api/events")
        self.assertEqual(response.status_code, 404)

        payload = response.get_json()
        self.assertIsInstance(payload, dict)
        self.assertIn("error", payload)
