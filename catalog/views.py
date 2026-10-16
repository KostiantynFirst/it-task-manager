from functools import cached_property

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import ProtectedError
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views import generic

from catalog.forms import (
    NameSearchForm,
    TaskForm,
    TaskSearchForm,
    WorkerCreationForm,
    WorkerSearchForm,
    WorkerUpdateForm,
)
from catalog.models import Worker, Task, TaskType, Position


class ProtectedDeleteView(LoginRequiredMixin, generic.DeleteView):

    template_name = "catalog/entity_confirm_delete.html"

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except ProtectedError:
            messages.error(
                self.request,
                f"Cannot delete {self.object}: it is still in use"
            )
            return HttpResponseRedirect(self.get_success_url())


class SearchListView(LoginRequiredMixin, generic.ListView):

    paginate_by = 5
    search_form_class = None
    search_param = "name"
    search_lookup = "name__icontains"

    @cached_property
    def search_form(self):
        return self.search_form_class(self.request.GET)

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.search_form.is_valid():
            search_term = self.search_form.cleaned_data[self.search_param]
            if search_term:
                queryset = queryset.filter(**{self.search_lookup: search_term})
            return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop("page", None)
        context["search_form"] = self.search_form
        context["query_string"] = params.urlencode()
        return context


class IndexView(LoginRequiredMixin, generic.TemplateView):
    template_name = "catalog/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        num_visits = self.request.session.get("num_visits", 0) + 1
        self.request.session["num_visits"] = num_visits
        context.update(
            num_workers=Worker.objects.count(),
            num_tasks=Task.objects.count(),
            num_completed=Task.objects.filter(is_completed=True).count(),
            num_pending=Task.objects.filter(is_completed=False).count(),
            num_visits=num_visits,
        )
        return context


class TaskListView(SearchListView):
    queryset = Task.objects.select_related("task_type").prefetch_related("assignees")
    search_form_class = TaskSearchForm

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.search_form.is_valid():
            status = self.search_form.cleaned_data["status"]
            priority = self.search_form.cleaned_data["priority"]
            if status == "completed":
                queryset = queryset.filter(is_completed=True)
            elif status == "pending":
                queryset = queryset.filter(is_completed=False)
            if priority:
                queryset = queryset.filter(priority=priority)
        return queryset


class TaskDetailView(LoginRequiredMixin, generic.DetailView):
    queryset = Task.objects.select_related("task_type").prefetch_related("assignees")


class TaskCreateView(LoginRequiredMixin, generic.CreateView):
    model = Task
    form_class = TaskForm
    success_url = reverse_lazy("catalog:task-list")


class TaskUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Task
    form_class = TaskForm
    success_url = reverse_lazy("catalog:task-list")


class TaskDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Task
    success_url = reverse_lazy("catalog:task-list")


class WorkerListView(SearchListView):
    queryset = Worker.objects.select_related("position")
    search_form_class = WorkerSearchForm
    search_param = "username"
    search_lookup = "username__icontains"


class WorkerDetailView(LoginRequiredMixin, generic.DetailView):
    queryset = Worker.objects.select_related("position")


class WorkerCreateView(LoginRequiredMixin, generic.CreateView):
    model = Worker
    form_class = WorkerCreationForm
    template_name = "catalog/entity_form.html"
    extra_context = {"entity": "worker"}
    success_url = reverse_lazy("catalog:worker-list")


class WorkerUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Worker
    form_class = WorkerUpdateForm
    template_name = "catalog/entity_form.html"
    extra_context = {"entity": "worker"}
    success_url = reverse_lazy("catalog:worker-list")


class WorkerDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Worker
    template_name = "catalog/entity_confirm_delete.html"
    success_url = reverse_lazy("catalog:worker-list")


class TaskTypeListView(SearchListView):
    model = TaskType
    search_form_class = NameSearchForm


class TaskTypeCreateView(LoginRequiredMixin, generic.CreateView):
    model = TaskType
    fields = ("name",)
    template_name = "catalog/entity_form.html"
    extra_context = {"entity": "task type"}
    success_url = reverse_lazy("catalog:task-type-list")


class TaskTypeUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = TaskType
    fields = ("name",)
    template_name = "catalog/entity_form.html"
    extra_context = {"entity": "task type"}
    success_url = reverse_lazy("catalog:task-type-list")


class TaskTypeDeleteView(ProtectedDeleteView):
    model = TaskType
    template_name = "catalog/entity_confirm_delete.html"
    success_url = reverse_lazy("catalog:task-type-list")


class PositionListView(SearchListView):
    model = Position
    search_form_class = NameSearchForm


class PositionCreateView(LoginRequiredMixin, generic.CreateView):
    model = Position
    fields = ("name",)
    template_name = "catalog/entity_form.html"
    extra_context = {"entity": "position"}
    success_url = reverse_lazy("catalog:position-list")


class PositionUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Position
    fields = ("name",)
    template_name = "catalog/entity_form.html"
    extra_context = {"entity": "position"}
    success_url = reverse_lazy("catalog:position-list")


class PositionDeleteView(ProtectedDeleteView):
    model = Position
    template_name = "catalog/entity_confirm_delete.html"
    success_url = reverse_lazy("catalog:position-list")
