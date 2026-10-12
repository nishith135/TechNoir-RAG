import unittest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


class TestAPI(unittest.TestCase):
    def test_root(self):
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("TechNoir RAG API", response.json().get("message", ""))

    def test_health(self):
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_version(self):
        response = client.get("/version")
        self.assertEqual(response.status_code, 200)
        self.assertIn("version", response.json())

    def test_unauthenticated_me(self):
        response = client.get("/auth/me")
        self.assertEqual(response.status_code, 401)

    def test_unauthenticated_collections(self):
        response = client.get("/collections")
        self.assertEqual(response.status_code, 401)

    def test_login_invalid_credentials(self):
        response = client.post("/auth/login", json={"email": "wrong@example.com", "password": "wrong"})
        self.assertEqual(response.status_code, 401)
        self.assertIn("detail", response.json())


if __name__ == "__main__":
    unittest.main()
