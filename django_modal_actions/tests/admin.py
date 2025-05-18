from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from django_modal_actions.mixins import (
    ModalActionMixin,
    modal_action,
    conditional_field,
)


class CustomForm(forms.Form):
    name = forms.CharField(label="Name", required=True)

    def clean_name(self):
        name = self.cleaned_data["name"]
        if name == "bad":
            raise forms.ValidationError("Name cannot be 'bad'")
        return name


class ConditionalForm(forms.Form):
    action_type = forms.ChoiceField(
        label="Action Type",
        choices=[("email", "Email"), ("sms", "SMS"), ("none", "No notification")],
        initial="none",
    )

    email_address = conditional_field(dependent_field="action_type", values=["email"])(
        forms.EmailField(label="Email Address", required=False)
    )

    phone_number = conditional_field(dependent_field="action_type", values=["sms"])(
        forms.CharField(label="Phone Number", required=False)
    )


class UserAdmin(ModalActionMixin, BaseUserAdmin):
    modal_actions = [
        "object_action",
        "object_action_with_form_class",
        "conditional_fields_action",
        "object_action_skip_confirmation",
    ]
    list_modal_actions = [
        "list_action",
        "list_action_with_form_class",
        "list_action_skip_confirmation",
    ]

    @modal_action(modal_header="Object Action")
    def object_action(self, request, obj, form_data=None):
        return "Object action works"

    @modal_action(modal_header="List Action")
    def list_action(self, request, queryset, form_data=None):
        return "List action works"

    @modal_action(modal_header="Object Action with Form Class", form_class=CustomForm)
    def object_action_with_form_class(self, request, obj, form_data=None):
        return "Object action with form class works"

    @modal_action(modal_header="List Action with Form Class", form_class=CustomForm)
    def list_action_with_form_class(self, request, queryset, form_data=None):
        return f"List action with form class works on {queryset.count()} items"

    @modal_action(
        modal_header="Conditional Fields Action",
        modal_description="Test conditional fields",
        form_class=ConditionalForm,
    )
    def conditional_fields_action(self, request, obj, form_data=None):
        if form_data and "action_type" in form_data:
            action_type = form_data["action_type"]
            if action_type == "email" and "email_address" in form_data:
                return f"Email will be sent to {form_data['email_address']}"
            elif action_type == "sms" and "phone_number" in form_data:
                return f"SMS will be sent to {form_data['phone_number']}"
            elif action_type == "none":
                return "No notification will be sent"
        return "Conditional fields action works"

    @modal_action(
        modal_header="Object Action Skip Confirmation", skip_confirmation=True
    )
    def object_action_skip_confirmation(self, request, obj, form_data=None):
        return "Object action without confirmation works"

    @modal_action(modal_header="List Action Skip Confirmation", skip_confirmation=True)
    def list_action_skip_confirmation(self, request, queryset, form_data=None):
        return f"List action without confirmation works on {queryset.count()} items"


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
