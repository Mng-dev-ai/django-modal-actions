# Django Modal Actions

Django Modal Actions is a reusable Django app that provides a convenient way to add modal-based actions to your Django admin interface. It allows you to create custom actions that open in a modal dialog, enhancing the user experience and functionality of your Django admin.

## Features

- Easy integration with Django admin
- Support for both list-view and object-view actions
- Customizable modal forms
- AJAX-based form submission

## Requirements

- Python (>= 3.7)
- Django (>= 3.2)

## Installation

1. Install the package using pip:

   ```
   pip install django-modal-actions
   ```

2. Add `'django_modal_actions'` to your `INSTALLED_APPS` setting:

   ```python
   INSTALLED_APPS = [
       ...
       'django_modal_actions',
       ...
   ]
   ```

## Usage

1. In your `admin.py`, import the necessary components:

   ```python
   from django.contrib import admin
   from django_modal_actions import ModalActionMixin, modal_action
   ```

2. Create a custom admin class that inherits from `ModalActionMixin` and your base admin class:

   ```python
   @admin.register(YourModel)
   class YourModelAdmin(ModalActionMixin, admin.ModelAdmin):
       modal_actions = ["your_object_action"]
       list_modal_actions = ["your_list_action"]

       @modal_action(modal_header="Object Action")
       def your_object_action(self, request, obj, form_data=None):
           # Your object action logic here
           return "Action completed successfully"

       @modal_action(modal_header="List Action")
       def your_list_action(self, request, queryset, form_data=None):
           # Your list action logic here
           return f"Action completed on {queryset.count()} items"
   ```

3. If you need a custom form for your action, create a form class:

   ```python
   from django import forms

   class CustomForm(forms.Form):
       name = forms.CharField(label="Name", required=True)

       def clean_name(self):
           name = self.cleaned_data["name"]
           if name == "bad":
               raise forms.ValidationError("Name cannot be 'bad'")
           return name
   ```

   Then, use it in your action:

   ```python
   @modal_action(modal_header="Action with Form", form_class=CustomForm)
   def your_action_with_form(self, request, obj, form_data=None):
       # Your action logic here
       return f"Action completed with name: {form_data['name']}"
   ```

## Testing

To run the tests, execute:

```
python -m unittest discover django_modal_actions/tests
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
