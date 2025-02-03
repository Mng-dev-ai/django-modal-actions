import json
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type, Union

from django.contrib import messages
from django.http import HttpRequest, JsonResponse
from django.template.loader import render_to_string
from django.urls import path, reverse
from django.utils.html import format_html


class ModalActionMixin:
    modal_actions: List[str] = []
    list_modal_actions: List[str] = []
    change_form_template: str = "admin/django_modal_actions/change_form.html"
    change_list_template: str = "admin/django_modal_actions/change_list.html"

    def get_urls(self) -> List[path]:
        urls: List[path] = super().get_urls()
        custom_urls = [
            path(
                "<path:object_id>/modal-action/<str:action>/",
                self.admin_site.admin_view(self.get_modal_content),
                name=f"{self.model._meta.app_label}_{self.model._meta.model_name}_modal_action",
            ),
            path(
                "<path:object_id>/execute-action/<str:action>/",
                self.admin_site.admin_view(self.execute_modal_action),
                name=f"{self.model._meta.app_label}_{self.model._meta.model_name}_execute_action",
            ),
            path(
                "list-modal-action/<str:action>/",
                self.admin_site.admin_view(self.get_modal_content),
                name=f"{self.model._meta.app_label}_{self.model._meta.model_name}_list_modal_action",
            ),
            path(
                "execute-list-action/<str:action>/",
                self.admin_site.admin_view(self.execute_modal_action),
                name=f"{self.model._meta.app_label}_{self.model._meta.model_name}_execute_list_action",
            ),
        ]
        return custom_urls + urls

    def get_modal_content(
        self, request: HttpRequest, action: str, object_id: Optional[str] = None
    ) -> JsonResponse:
        obj = self.get_object(request, object_id) if object_id else None
        action_func: Callable = getattr(self, action)
        form_class: Optional[Type] = getattr(action_func, "form_class", None)
        form = form_class(request.POST or None) if form_class else None

        if obj is None:
            selected_ids = json.loads(request.GET.get("selected_ids", "[]"))
            queryset = self.model.objects.filter(pk__in=selected_ids)
            description = (
                getattr(action_func, "modal_description", None)
                or f"Are you sure you want to perform this action on {queryset.count()} items?"
            )
        else:
            description = (
                getattr(action_func, "modal_description", None)
                or f"Are you sure you want to perform this action on {obj}?"
            )

        context = {
            "object": obj,
            "action": action,
            "action_name": getattr(action_func, "modal_header", None)
            or action.replace("_", " ").title(),
            "description": description,
            "opts": self.model._meta,
            "form": form,
            "selected_ids": json.dumps(selected_ids) if obj is None else None,
        }
        content = render_to_string(
            "admin/django_modal_actions/modal_actions.html", context, request
        )
        return JsonResponse({"content": content})

    def execute_modal_action(
        self, request: HttpRequest, action: str, object_id: Optional[str] = None
    ) -> JsonResponse:
        action_func: Callable = getattr(self, action)
        form_class: Optional[Type] = getattr(action_func, "form_class", None)
        try:
            if object_id:
                obj = self.get_object(request, object_id)
                queryset_or_obj = obj
            else:
                selected_ids = json.loads(request.POST.get("selected_ids", "[]"))
                queryset_or_obj = self.model.objects.filter(pk__in=selected_ids)

            if not self.has_action_permission(
                request, action, obj if object_id else None
            ):
                return JsonResponse(
                    {"success": False, "errors": {"__all__": ["Permission denied"]}}
                )
            if form_class:
                form = form_class(request.POST, request.FILES)
                if form.is_valid():
                    response = action_func(request, queryset_or_obj, form.cleaned_data)
                    self.message_user(request, str(response), messages.SUCCESS)
                    return JsonResponse({"success": True})
                return JsonResponse({"success": False, "errors": form.errors})
            response = action_func(request, queryset_or_obj)
            self.message_user(request, str(response), messages.SUCCESS)
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "errors": {"__all__": [str(e)]}})

    def get_modal_action_buttons(self, obj=None) -> str:
        buttons: List[str] = []
        actions = self.list_modal_actions if obj is None else self.modal_actions
        for action in actions:
            if self.has_action_permission(self.request, action, obj):
                func = getattr(self, action)
                if obj:
                    url = reverse(
                        f"admin:{obj._meta.app_label}_{obj._meta.model_name}_modal_action",
                        args=[obj.pk, action],
                    )
                else:
                    url = reverse(
                        f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_list_modal_action",
                        args=[action],
                    )
                buttons.append(
                    format_html(
                        '<a class="historylink dma-modal-action-button" href="{}">{}</a>',
                        url,
                        getattr(
                            func, "short_description", action.replace("_", " ").upper()
                        ),
                    )
                )
        return format_html("".join(buttons))

    def change_view(
        self,
        request: HttpRequest,
        object_id: str,
        form_url: str = "",
        extra_context: Optional[Dict[str, Any]] = None,
    ):
        self.request = request
        extra_context = extra_context or {}
        extra_context["modal_action_buttons"] = self.get_modal_action_buttons(
            self.get_object(request, object_id)
        )
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context
        )

    def changelist_view(
        self, request: HttpRequest, extra_context: Optional[Dict[str, Any]] = None
    ):
        self.request = request
        extra_context = extra_context or {}
        extra_context["list_modal_action_buttons"] = self.get_modal_action_buttons()
        return super().changelist_view(request, extra_context=extra_context)

    def has_action_permission(
        self, request: HttpRequest, action: str, obj: Optional[object] = None
    ) -> bool:
        action_func: Optional[Callable] = getattr(self, action, None)
        if not action_func:
            return True

        permissions = getattr(action_func, "permissions", None)
        if not permissions:
            return True

        if not isinstance(permissions, (list, tuple)):
            permissions = [permissions]

        try:
            return all(p(request, obj) for p in permissions)
        except TypeError as e:
            raise ValueError(f"Invalid permission check: {e}") from e

    class Media:
        js = ("admin/js/jquery.init.js", "django_modal_actions/js/modal_actions.js")
        css = {"all": ("django_modal_actions/css/modal_actions.css",)}


def modal_action(
    modal_header: Optional[str] = None,
    modal_description: Optional[str] = None,
    permissions: Optional[Union[Callable, List[Callable]]] = None,
    form_class: Optional[Type] = None,
):
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, queryset_or_obj, form_data=None):
            return func(self, request, queryset_or_obj, form_data)

        wrapper.modal_header = modal_header
        wrapper.modal_description = modal_description
        wrapper.permissions = permissions
        wrapper.form_class = form_class
        return wrapper

    return decorator
