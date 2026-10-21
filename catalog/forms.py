from django import forms
from django.contrib.auth.forms import UserCreationForm
from catalog.models import Task, Worker


def search_input(placeholder):
    return forms.TextInput(
        attrs={"class": "form-control", "placeholder": placeholder}
    )


class SearchForm(forms.Form):
    search_field = "name"
    search_lookup = "name__icontains"

    def filter_queryset(self, queryset):
        if not self.is_valid():
            return queryset
        term = self.cleaned_data.get(self.search_field)
        if term:
            queryset = queryset.filter(**{self.search_lookup: term})
        return queryset


class NameSearchForm(SearchForm):
    name = forms.CharField(
        max_length=255,
        required=False,
        label="",
        widget=search_input("Search by name"),
    )


class TaskSearchForm(NameSearchForm):
    STATUS_CHOICES = (
        ("", "All statuses"),
        ("completed", "Completed"),
        ("pending", "Pending"),
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

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        if not self.is_valid():
            return queryset
        status = self.cleaned_data["status"]
        priority = self.cleaned_data["priority"]
        if status == "completed":
            queryset = queryset.filter(is_completed=True)
        elif status == "pending":
            queryset = queryset.filter(is_completed=False)
        if priority:
            queryset = queryset.filter(priority=priority)
        return queryset


class WorkerSearchForm(SearchForm):
    search_field = "username"
    search_lookup = "username__icontains"

    username = forms.CharField(
        max_length=150,
        required=False,
        label="",
        widget=search_input("Search by username"),
    )


class PositionRequiredMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["position"].required = True


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


class WorkerCreationForm(PositionRequiredMixin, UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Worker
        fields = UserCreationForm.Meta.fields + (
            "first_name",
            "last_name",
            "email",
            "position",
        )


class WorkerUpdateForm(PositionRequiredMixin, forms.ModelForm):
    class Meta:
        model = Worker
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "position",
        )
