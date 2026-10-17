from datetime import timedelta

from django.db.models import ProtectedError
from django.urls import reverse

from catalog.models import Task, Worker
from catalog.tests.base import PASSWORD, BaseTestCase


class StrMethodTests(BaseTestCase):
    def test_position_str(self):
        self.assertEqual(str(self.position), "Developer")

    def test_task_type_str(self):
        self.assertEqual(str(self.task_type), "Bug")

    def test_worker_str(self):
        self.assertEqual(str(self.worker), "john (John Doe)")

    def test_task_str(self):
        task = self.create_task(name="Fix dashboard")
        self.assertEqual(str(task), "Fix dashboard (Medium)")


class WorkerModelTests(BaseTestCase):
    def test_get_absolute_url(self):
        self.assertEqual(
            self.worker.get_absolute_url(),
            reverse("catalog:worker-detail", args=[self.worker.pk]),
        )

    def test_worker_can_be_created_without_position(self):
        worker = Worker.objects.create_user(username="nopos", password=PASSWORD)
        self.assertIsNone(worker.position)

    def test_position_with_workers_cannot_be_deleted(self):
        with self.assertRaises(ProtectedError):
            self.position.delete()


class TaskModelTests(BaseTestCase):
    def test_default_values(self):
        task = self.create_task()
        self.assertEqual(task.priority, Task.Priority.MEDIUM)
        self.assertFalse(task.is_completed)

    def test_task_type_with_tasks_cannot_be_deleted(self):
        self.create_task()
        with self.assertRaises(ProtectedError):
            self.task_type.delete()

    def test_ordering_is_completed_then_deadline(self):
        completed_task = self.create_task(
            name="Done",
            is_completed=True,
            deadline=self.today - timedelta(days=5),
        )
        late_task = self.create_task(name="Late", deadline=self.today + timedelta(days=5))
        soon_task = self.create_task(name="Soon", deadline=self.today + timedelta(days=1))
        self.assertEqual(
            list(Task.objects.all()),
            [soon_task, late_task, completed_task],
        )

    def test_task_with_past_deadline_is_overdue(self):
        task = self.create_task(deadline=self.today - timedelta(days=1))
        self.assertTrue(task.is_overdue)

    def test_completed_task_is_not_overdue(self):
        task = self.create_task(
            deadline=self.today - timedelta(days=1),
            is_completed=True,
        )
        self.assertFalse(task.is_overdue)

    def test_task_due_today_is_not_overdue(self):
        task = self.create_task(deadline=self.today)
        self.assertFalse(task.is_overdue)

    def test_task_with_future_deadline_is_not_overdue(self):
        task = self.create_task(deadline=self.today + timedelta(days=1))
        self.assertFalse(task.is_overdue)
