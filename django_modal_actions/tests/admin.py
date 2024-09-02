from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from django_modal_actions.mixins import ModalActionMixin, modal_action


class CustomForm(forms.Form):
    name = forms.CharField(label="Name", required=True)

    def clean_name(self):
        name = self.cleaned_data["name"]
        if name == "bad":
            raise forms.ValidationError("Name cannot be 'bad'")
        return name


class UserAdmin(ModalActionMixin, BaseUserAdmin):
    modal_actions = ["object_action", "object_action_with_form_class"]
    list_modal_actions = ["list_action", "list_action_with_form_class"]

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


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
