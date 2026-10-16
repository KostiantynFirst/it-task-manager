from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from catalog.models import Task, Worker


def search_input(placeholder):
    return forms.TextInput(
        attrs={"class": "form-control", "placeholder": placeholder}
    )


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = (
            "name",
            "description",
            "deadline",
            "priority",
            "task_type",
            "assignees",
        )
        widgets = {
            "deadline": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "assignees": forms.CheckboxSelectMultiple(),
        }

    def clean_deadline(self):
        deadline = self.cleaned_data["deadline"]
        if "deadline" in self.changed_data and deadline < timezone.localdate():
            raise forms.ValidationError("Deadline cannot be earlier than today.")
        return deadline


class WorkerCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Worker
        fields = UserCreationForm.Meta.fields + (
            "first_name",
            "last_name",
            "email",
            "position",
        )


class WorkerUpdateForm(forms.ModelForm):
    class Meta:
        model = Worker
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "position",
        )


class TaskSearchForm(forms.Form):
    STATUS_CHOICES = (("", "All statuses"), ("completed", "Completed"), ("pending", "Pending"),)

    name = forms.CharField(
        max_length=255,
        required=False,
        label="",
        widget=search_input("Search by name"),
    )
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        label="",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    priority = forms.ChoiceField(
        choices=[("", "All priorities")] + list(Task.Priority.choices),
        required=False,
        label="",
        widget=forms.Select(attrs={"class": "form-select"}),
    )


class WorkerSearchForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        required=False,
        label="",
        widget=search_input("Search by username"),
    )


class NameSearchForm(forms.Form):
    name = forms.CharField(
        max_length=255,
        required=False,
        label="",
        widget=search_input("Search by name"),
    )
