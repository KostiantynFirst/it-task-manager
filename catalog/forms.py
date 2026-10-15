from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone

from catalog.models import Task, Worker


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
