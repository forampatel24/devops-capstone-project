
"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase

from tests.factories import AccountFactory
from service.common import status
from service.models import db, Account, init_db
from service.routes import app

DATABASE_URI = os.getenv(
    "DATABASE_URI",
    "postgresql://postgres:postgres@localhost:5432/postgres",
)

BASE_URL = "/accounts"


######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Runs once before all tests"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()
        db.session.commit()
        self.client = app.test_client()

    def tearDown(self):
        """Runs after each test case"""
        db.session.remove()

    ##################################################################
    #  H E L P E R   M E T H O D S
    ##################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(
                BASE_URL,
                json=account.serialize(),
            )
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ##################################################################
    #  A C C O U N T   T E S T   C A S E S
    ##################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json",
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        location = response.headers.get("Location")
        self.assertIsNotNone(location)

        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(
            new_account["phone_number"],
            account.phone_number,
        )
        self.assertEqual(
            new_account["date_joined"],
            str(account.date_joined),
        )

    def test_bad_request(self):
        """It should reject incomplete account data"""
        response = self.client.post(
            BASE_URL,
            json={"name": "not enough data"},
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_unsupported_media_type(self):
        """It should reject an unsupported media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            data=account.serialize().__str__(),
            content_type="text/plain",
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )

    def test_read_an_account(self):
        """It should Read an Account"""
        account = AccountFactory()

        create_response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json",
        )
        self.assertEqual(
            create_response.status_code,
            status.HTTP_201_CREATED,
        )

        new_account = create_response.get_json()
        account_id = new_account["id"]

        response = self.client.get(f"{BASE_URL}/{account_id}")
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        data = response.get_json()
        self.assertEqual(data["id"], account_id)
        self.assertEqual(data["name"], account.name)
        self.assertEqual(data["email"], account.email)
        self.assertEqual(data["address"], account.address)
        self.assertEqual(
            data["phone_number"],
            account.phone_number,
        )

    def test_read_account_not_found(self):
        """It should return 404 for a nonexistent account"""
        response = self.client.get(f"{BASE_URL}/0")
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
