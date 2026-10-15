from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views import generic

from catalog.forms import TaskForm
from catalog.models import Worker, Task


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


class TaskListView(LoginRequiredMixin, generic.ListView):
    queryset = Task.objects.select_related("task_type").prefetch_related("assignees")


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
