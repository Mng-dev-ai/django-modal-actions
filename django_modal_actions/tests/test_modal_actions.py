# ruff: noqa: E402
import os

import django

os.environ["DJANGO_SETTINGS_MODULE"] = "django_modal_actions.tests.test_settings"
django.setup()

import time

from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.management import call_command
from django.db import connection
from django.test import Client
from django.urls import reverse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class DjangoModalActionsTests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if connection.vendor == "sqlite":
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys = OFF;")
            cursor.close()

        call_command("migrate")

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        cls.selenium = webdriver.Chrome(options=chrome_options)
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpassword"
        )
        self.client = Client()
        self.client.login(username="admin", password="adminpassword")

        session_id = self.client.cookies["sessionid"].value
        self.selenium.get(f"{self.live_server_url}/admin/")
        self.selenium.add_cookie(
            {"name": "sessionid", "value": session_id, "path": "/"}
        )

    def open_modal(self, action_name):
        modal_button = WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, action_name))
        )
        modal_button.click()
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, "dma-modal-action"))
        )
        time.sleep(1)  # Allow for any animations to complete

    def submit_form(self, name_value):
        name_field = WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, "id_name"))
        )
        name_field.clear()
        name_field.send_keys(name_value)
        submit_button = WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "#dma-modal-action button[type='submit']")
            )
        )
        self.selenium.execute_script("arguments[0].click();", submit_button)

    def test_list_modal_action_button_appears(self):
        self.selenium.get(self.live_server_url + reverse("admin:auth_user_changelist"))
        modal_button = self.selenium.find_element(
            By.LINK_TEXT, "LIST ACTION WITH FORM CLASS"
        )
        self.assertIsNotNone(modal_button)

    def test_object_modal_action_button_appears(self):
        user = User.objects.first()
        self.selenium.get(
            self.live_server_url + reverse("admin:auth_user_change", args=[user.id])
        )
        modal_button = self.selenium.find_element(By.LINK_TEXT, "OBJECT ACTION")
        self.assertIsNotNone(modal_button)

    def test_form_validation_invalid_input(self):
        self.selenium.get(self.live_server_url + reverse("admin:auth_user_changelist"))
        self.open_modal("LIST ACTION WITH FORM CLASS")
        self.submit_form("bad")

        error_list = WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "dma-errorlist"))
        )
        self.assertIn("Name cannot be 'bad'", error_list.text)

    def test_form_submission_valid_input(self):
        self.selenium.get(self.live_server_url + reverse("admin:auth_user_changelist"))
        self.open_modal("LIST ACTION WITH FORM CLASS")
        self.submit_form("good_name")

        # Wait for the modal to close
        WebDriverWait(self.selenium, 10).until(
            EC.invisibility_of_element_located((By.ID, "dma-modal-action"))
        )

        # Check for success message
        success_message = WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "success"))
        )
        self.assertIn(
            "List action with form class works on 0 items", success_message.text
        )

    def test_modal_closes_on_cancel(self):
        self.selenium.get(self.live_server_url + reverse("admin:auth_user_changelist"))
        self.open_modal("LIST ACTION WITH FORM CLASS")

        # Ensure the modal is visible
        modal = WebDriverWait(self.selenium, 10).until(
            EC.visibility_of_element_located((By.ID, "dma-modal-action"))
        )
        self.assertTrue(modal.is_displayed())

        cancel_button = WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "#dma-modal-action button.cancel")
            )
        )
        cancel_button.click()

        # Wait for the modal to become invisible
        WebDriverWait(self.selenium, 10).until(
            EC.invisibility_of_element_located((By.ID, "dma-modal-action"))
        )

        # Check if the modal is no longer visible
        modal = self.selenium.find_element(By.ID, "dma-modal-action")
        self.assertFalse(modal.is_displayed())

    def test_object_modal_form_submission(self):
        user = User.objects.first()
        self.selenium.get(
            self.live_server_url + reverse("admin:auth_user_change", args=[user.id])
        )
        self.open_modal("OBJECT ACTION WITH FORM CLASS")
        self.submit_form("good_name")

        # Wait for the modal to close
        WebDriverWait(self.selenium, 10).until(
            EC.invisibility_of_element_located((By.ID, "dma-modal-action"))
        )

        # Check for success message
        success_message = WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "success"))
        )
        self.assertIn("Object action with form class works", success_message.text)


if __name__ == "__main__":
    import unittest

    unittest.main()
