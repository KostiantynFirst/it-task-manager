from functools import cached_property
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, ProtectedError, Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
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
from catalog.models import (
    Worker,
    Task,
    TaskType,
    Position
)
from catalog.mixins import (
    StaffOrAssigneeRequiredMixin,
    StaffOrSelfRequiredMixin,
    StaffRequiredMixin,
)


class ProtectedDeleteView(StaffRequiredMixin, generic.DeleteView):

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
    search_form_class = NameSearchForm

    @cached_property
    def search_form(self):
        return self.search_form_class(self.request.GET)

    def get_queryset(self):
        return self.search_form.filter_queryset(super().get_queryset())

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
        task_stats = Task.objects.aggregate(
            num_tasks=Count("pk"),
            num_completed=Count("pk", filter=Q(is_completed=True)),
            num_pending=Count("pk", filter=Q(is_completed=False)),
        )
        context.update(
            task_stats,
            num_workers=Worker.objects.count(),
            num_visits=num_visits,
        )
        return context


class TaskListView(SearchListView):
    queryset = Task.objects.select_related("task_type").prefetch_related("assignees")
    search_form_class = TaskSearchForm


class TaskDetailView(LoginRequiredMixin, generic.DetailView):
    queryset = Task.objects.select_related("task_type").prefetch_related("assignees")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        is_assigned = user in self.object.assignees.all()
        context["is_assigned"] = is_assigned
        context["can_edit"] = user.is_staff or is_assigned
        return context


class TaskCreateView(LoginRequiredMixin, generic.CreateView):
    model = Task
    form_class = TaskForm
    success_url = reverse_lazy("catalog:task-list")


class TaskUpdateView(StaffOrAssigneeRequiredMixin, generic.UpdateView):
    model = Task
    form_class = TaskForm
    success_url = reverse_lazy("catalog:task-list")


class TaskDeleteView(StaffRequiredMixin, generic.DeleteView):
    model = Task
    success_url = reverse_lazy("catalog:task-list")


class TaskActionView(LoginRequiredMixin, generic.View):
    """POST-only action that sets an explicit target state."""

    def apply(self, task):
        raise NotImplementedError

    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        self.apply(task)
        return redirect("catalog:task-detail", pk=pk)


class TaskAssignMeView(TaskActionView):
    def apply(self, task):
        task.assignees.add(self.request.user)


class TaskUnassignMeView(TaskActionView):
    def apply(self, task):
        task.assignees.remove(self.request.user)


class TaskCompleteView(StaffOrAssigneeRequiredMixin, TaskActionView):
    def apply(self, task):
        Task.objects.filter(pk=task.pk).update(is_completed=True)


class TaskReopenView(StaffOrAssigneeRequiredMixin, TaskActionView):
    def apply(self, task):
        Task.objects.filter(pk=task.pk).update(is_completed=False)


class WorkerListView(SearchListView):
    queryset = Worker.objects.select_related("position")
    search_form_class = WorkerSearchForm


class WorkerDetailView(LoginRequiredMixin, generic.DetailView):
    queryset = Worker.objects.select_related("position")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tasks = self.object.tasks.select_related("task_type")
        context["completed_tasks"] = tasks.filter(is_completed=True)
        context["pending_tasks"] = tasks.filter(is_completed=False)
        return context


class WorkerCreateView(StaffRequiredMixin, generic.CreateView):
    model = Worker
    form_class = WorkerCreationForm
    template_name = "catalog/entity_form.html"
    extra_context = {"entity": "worker"}
    success_url = reverse_lazy("catalog:worker-list")


class WorkerUpdateView(StaffOrSelfRequiredMixin, generic.UpdateView):
    model = Worker
    form_class = WorkerUpdateForm
    template_name = "catalog/entity_form.html"
    extra_context = {"entity": "worker"}
    success_url = reverse_lazy("catalog:worker-list")


class WorkerDeleteView(StaffRequiredMixin, generic.DeleteView):
    model = Worker
    template_name = "catalog/entity_confirm_delete.html"
    success_url = reverse_lazy("catalog:worker-list")

    def form_valid(self, form):
        if self.object.tasks.exists():
            messages.error(
                self.request,
                f"Cannot delete {self.object}: the worker is assigned to tasks."
            )
            return redirect("catalog:worker-detail", pk=self.object.pk)
        return super().form_valid(form)


class TaskTypeListView(SearchListView):
    model = TaskType
    search_form_class = NameSearchForm


class TaskTypeCreateView(StaffRequiredMixin, generic.CreateView):
    model = TaskType
    fields = ("name",)
    template_name = "catalog/entity_form.html"
    extra_context = {"entity": "task type"}
    success_url = reverse_lazy("catalog:task-type-list")


class TaskTypeUpdateView(StaffRequiredMixin, generic.UpdateView):
    model = TaskType
    fields = ("name",)
    template_name = "catalog/entity_form.html"
    extra_context = {"entity": "task type"}
    success_url = reverse_lazy("catalog:task-type-list")


class TaskTypeDeleteView(ProtectedDeleteView):
    model = TaskType
    success_url = reverse_lazy("catalog:task-type-list")


class PositionListView(SearchListView):
    model = Position
    search_form_class = NameSearchForm


class PositionCreateView(StaffRequiredMixin, generic.CreateView):
    model = Position
    fields = ("name",)
    template_name = "catalog/entity_form.html"
    extra_context = {"entity": "position"}
    success_url = reverse_lazy("catalog:position-list")


class PositionUpdateView(StaffRequiredMixin, generic.UpdateView):
    model = Position
    fields = ("name",)
    template_name = "catalog/entity_form.html"
    extra_context = {"entity": "position"}
    success_url = reverse_lazy("catalog:position-list")


class PositionDeleteView(ProtectedDeleteView):
    model = Position
    success_url = reverse_lazy("catalog:position-list")
