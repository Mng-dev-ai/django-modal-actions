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
from selenium.webdriver.support.ui import WebDriverWait, Select


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

    def test_button_disables_on_form_submission(self):
        self.selenium.get(self.live_server_url + reverse("admin:auth_user_changelist"))
        self.open_modal("LIST ACTION WITH FORM CLASS")

        name_field = WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, "id_name"))
        )
        name_field.clear()
        name_field.send_keys("good_name")

        submit_button = WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "#dma-modal-action button[type='submit']")
            )
        )

        self.assertFalse(submit_button.get_attribute("disabled"))

        was_disabled = self.selenium.execute_script(
            """
            var $button = django.jQuery(arguments[0]);
            $button.click();
            return $button.prop('disabled');
        """,
            submit_button,
        )

        self.assertTrue(was_disabled)

    def test_spinner_visible_during_submission(self):
        self.selenium.get(self.live_server_url + reverse("admin:auth_user_changelist"))
        self.open_modal("LIST ACTION WITH FORM CLASS")

        name_field = WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, "id_name"))
        )
        name_field.clear()
        name_field.send_keys("good_name")

        spinner = WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".dma-confirm-btn .dma-spinner")
            )
        )

        is_hidden_initially = self.selenium.execute_script(
            'return django.jQuery(arguments[0]).css("display") === "none";', spinner
        )
        self.assertTrue(is_hidden_initially)

        submit_button = WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "#dma-modal-action button[type='submit']")
            )
        )

        was_visible = self.selenium.execute_script(
            """
            var $button = django.jQuery(arguments[0]);
            $button.click();
            var $spinner = django.jQuery('.dma-confirm-btn .dma-spinner');
            var display = $spinner.css('display');
            return display === 'inline-block' || display === 'inline' || $spinner.is(':visible');
        """,
            submit_button,
        )

        self.assertTrue(was_visible)

    def test_aria_busy_attribute_during_submission(self):
        self.selenium.get(self.live_server_url + reverse("admin:auth_user_changelist"))
        self.open_modal("LIST ACTION WITH FORM CLASS")

        name_field = WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, "id_name"))
        )
        name_field.clear()
        name_field.send_keys("good_name")

        submit_button = WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "#dma-modal-action button[type='submit']")
            )
        )

        initial_aria_busy = submit_button.get_attribute("aria-busy")
        self.assertIn(initial_aria_busy, [None, "false"])

        aria_busy_was_true = self.selenium.execute_script(
            """
            var $button = django.jQuery(arguments[0]);
            $button.click();
            return $button.attr('aria-busy') === 'true';
        """,
            submit_button,
        )

        self.assertTrue(aria_busy_was_true)

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

    def test_conditional_fields(self):
        user = User.objects.first()
        self.selenium.get(
            self.live_server_url + reverse("admin:auth_user_change", args=[user.id])
        )
        self.open_modal("CONDITIONAL FIELDS ACTION")

        # Wait for the form to be fully loaded and initial state to be set
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, "id_action_type"))
        )

        # Check initial state (should be 'none' and both fields hidden)
        email_field_visible = self.selenium.execute_script(
            'return django.jQuery("#id_email_address").closest("p").is(":visible");'
        )
        phone_field_visible = self.selenium.execute_script(
            'return django.jQuery("#id_phone_number").closest("p").is(":visible");'
        )
        self.assertFalse(email_field_visible, "Email field should be hidden initially")
        self.assertFalse(phone_field_visible, "Phone field should be hidden initially")

        # Select email type
        action_type_select = Select(self.selenium.find_element(By.ID, "id_action_type"))
        action_type_select.select_by_value("email")

        # Wait for the change event to be processed and check visibility
        WebDriverWait(self.selenium, 10).until(
            lambda driver: driver.execute_script(
                'return django.jQuery("#id_email_address").closest("p").is(":visible");'
            )
        )

        # Verify email field is visible and phone field is hidden
        email_field_visible = self.selenium.execute_script(
            'return django.jQuery("#id_email_address").closest("p").is(":visible");'
        )
        phone_field_visible = self.selenium.execute_script(
            'return django.jQuery("#id_phone_number").closest("p").is(":visible");'
        )
        self.assertTrue(
            email_field_visible,
            "Email field should be visible when email type is selected",
        )
        self.assertFalse(
            phone_field_visible,
            "Phone field should be hidden when email type is selected",
        )

        # Select SMS type
        action_type_select.select_by_value("sms")

        # Wait for the change event to be processed and check visibility
        WebDriverWait(self.selenium, 10).until(
            lambda driver: driver.execute_script(
                'return django.jQuery("#id_phone_number").closest("p").is(":visible");'
            )
        )

        # Verify phone field is visible and email field is hidden
        email_field_visible = self.selenium.execute_script(
            'return django.jQuery("#id_email_address").closest("p").is(":visible");'
        )
        phone_field_visible = self.selenium.execute_script(
            'return django.jQuery("#id_phone_number").closest("p").is(":visible");'
        )
        self.assertFalse(
            email_field_visible,
            "Email field should be hidden when SMS type is selected",
        )
        self.assertTrue(
            phone_field_visible,
            "Phone field should be visible when SMS type is selected",
        )

        # Test form submission with phone number
        phone_field = self.selenium.find_element(By.ID, "id_phone_number")
        phone_field.send_keys("123-456-7890")

        # Submit the form
        submit_button = WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "#dma-modal-action button[type='submit']")
            )
        )
        self.selenium.execute_script("arguments[0].click();", submit_button)

        # Wait for the modal to close
        WebDriverWait(self.selenium, 10).until(
            EC.invisibility_of_element_located((By.ID, "dma-modal-action"))
        )

        # Check for success message
        success_message = WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "success"))
        )
        self.assertIn("SMS will be sent to 123-456-7890", success_message.text)

    def test_skip_confirmation_object_action(self):
        user = User.objects.first()
        self.selenium.get(
            self.live_server_url + reverse("admin:auth_user_change", args=[user.id])
        )

        # Click the action button
        modal_button = WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable(
                (By.LINK_TEXT, "OBJECT ACTION SKIP CONFIRMATION")
            )
        )
        modal_button.click()

        # Page should reload directly without showing modal
        # Check for success message
        success_message = WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "success"))
        )
        self.assertIn("Object action without confirmation works", success_message.text)

        # Verify modal was never shown
        modal = self.selenium.find_element(By.ID, "dma-modal-action")
        self.assertFalse(modal.is_displayed())

    def test_skip_confirmation_list_action(self):
        self.selenium.get(self.live_server_url + reverse("admin:auth_user_changelist"))

        # Select some users
        checkboxes = self.selenium.find_elements(By.NAME, "_selected_action")
        if checkboxes:
            checkboxes[0].click()

        # Click the action button
        modal_button = WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "LIST ACTION SKIP CONFIRMATION"))
        )
        modal_button.click()

        # Page should reload directly without showing modal
        # Check for success message
        success_message = WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "success"))
        )
        self.assertIn("List action without confirmation works", success_message.text)

    def test_modal_action_validation_error(self):
        """Test that using form_class with skip_confirmation raises a ValueError"""
        from django_modal_actions.mixins import modal_action
        from django_modal_actions.tests.admin import CustomForm

        with self.assertRaises(ValueError) as cm:

            @modal_action(form_class=CustomForm, skip_confirmation=True)
            def invalid_action(self, request, obj, form_data=None):
                pass

        self.assertIn("Cannot use form_class with skip_confirmation", str(cm.exception))


if __name__ == "__main__":
    import unittest

    unittest.main()
