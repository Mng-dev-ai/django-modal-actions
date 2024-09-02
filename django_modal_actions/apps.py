import os

from django.apps import AppConfig


class DjangoModalActionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_modal_actions"
    path = os.path.dirname(os.path.abspath(__file__))
