from catalog.forms import NameSearchForm, TaskSearchForm, WorkerSearchForm
from catalog.models import Task, TaskType, Worker
from catalog.tests.base import BaseTestCase


class SearchFormTests(BaseTestCase):
    def test_name_form_filters_by_name(self):
        form = NameSearchForm({"name": "bu"})
        self.assertEqual(
            list(form.filter_queryset(TaskType.objects.all())),
            [self.task_type],
        )

    def test_worker_form_filters_by_username(self):
        form = WorkerSearchForm({"username": "jo"})
        self.assertEqual(
            list(form.filter_queryset(Worker.objects.all())),
            [self.worker],
        )

    def test_task_form_filters_by_status(self):
        self.create_task(name="Open")
        done = self.create_task(name="Done", is_completed=True)
        form = TaskSearchForm({"status": "completed"})
        self.assertEqual(list(form.filter_queryset(Task.objects.all())), [done])

    def test_task_form_filters_by_priority(self):
        self.create_task(name="Normal")
        urgent = self.create_task(name="Hot", priority=Task.Priority.URGENT)
        form = TaskSearchForm({"priority": "Urgent"})
        self.assertEqual(list(form.filter_queryset(Task.objects.all())), [urgent])

    def test_invalid_form_returns_queryset_unchanged(self):
        self.create_task()
        form = TaskSearchForm({"status": "bogus"})
        self.assertEqual(form.filter_queryset(Task.objects.all()).count(), 1)

    def test_task_form_filters_by_pending_status(self):
        open_task = self.create_task(name="Open")
        self.create_task(name="Done", is_completed=True)
        form = TaskSearchForm({"status": "pending"})
        self.assertEqual(list(form.filter_queryset(Task.objects.all())), [open_task])

    def test_search_is_case_insensitive(self):
        form = NameSearchForm({"name": "BUG"})
        self.assertEqual(
            list(form.filter_queryset(TaskType.objects.all())),
            [self.task_type],
        )
