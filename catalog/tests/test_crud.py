from datetime import timedelta

from django.urls import reverse

from catalog.models import Position, Task, TaskType, Worker
from catalog.tests.base import PASSWORD, LoggedInTestCase


class TaskCrudTests(LoggedInTestCase):
    def build_form_data(self, **overrides):
        form_data = {
            "name": "New task",
            "description": "Task description",
            "deadline": self.today + timedelta(days=3),
            "priority": Task.Priority.HIGH.value,
            "task_type": self.task_type.pk,
            "assignees": [self.worker.pk],
        }
        form_data.update(overrides)
        return form_data

    def test_create_task(self):
        response = self.client.post(
            reverse("catalog:task-create"),
            self.build_form_data(),
        )
        self.assertRedirects(response, reverse("catalog:task-list"))
        task = Task.objects.get(name="New task")
        self.assertEqual(task.priority, Task.Priority.HIGH)
        self.assertEqual(list(task.assignees.all()), [self.worker])

    def test_create_task_without_assignees(self):
        self.client.post(
            reverse("catalog:task-create"),
            self.build_form_data(assignees=[]),
        )
        self.assertEqual(Task.objects.get(name="New task").assignees.count(), 0)

    def test_create_task_with_deadline_today(self):
        self.client.post(
            reverse("catalog:task-create"),
            self.build_form_data(deadline=self.today),
        )
        self.assertTrue(Task.objects.filter(name="New task").exists())

    def test_create_task_with_past_deadline_is_rejected(self):
        response = self.client.post(
            reverse("catalog:task-create"),
            self.build_form_data(deadline=self.today - timedelta(days=1)),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"],
            "deadline",
            "Deadline cannot be earlier than today.",
        )
        self.assertFalse(Task.objects.exists())

    def test_overdue_task_can_be_edited_without_changing_deadline(self):
        past_date = self.today - timedelta(days=3)
        task = self.create_task(deadline=past_date)
        response = self.client.post(
            reverse("catalog:task-update", args=[task.pk]),
            self.build_form_data(name="Renamed", deadline=past_date),
        )
        self.assertRedirects(response, reverse("catalog:task-list"))
        task.refresh_from_db()
        self.assertEqual(task.name, "Renamed")

    def test_changing_deadline_to_past_is_rejected(self):
        task = self.create_task()
        response = self.client.post(
            reverse("catalog:task-update", args=[task.pk]),
            self.build_form_data(deadline=self.today - timedelta(days=1)),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("deadline", response.context["form"].errors)

    def test_delete_task(self):
        task = self.create_task()
        response = self.client.post(reverse("catalog:task-delete", args=[task.pk]))
        self.assertRedirects(response, reverse("catalog:task-list"))
        self.assertFalse(Task.objects.filter(pk=task.pk).exists())


class WorkerCrudTests(LoggedInTestCase):
    def build_creation_data(self, **overrides):
        form_data = {
            "username": "anna",
            "password1": PASSWORD,
            "password2": PASSWORD,
            "first_name": "Anna",
            "last_name": "Smith",
            "email": "anna@example.com",
            "position": self.position.pk,
        }
        form_data.update(overrides)
        return form_data

    def test_create_worker(self):
        response = self.client.post(
            reverse("catalog:worker-create"),
            self.build_creation_data(),
        )
        self.assertRedirects(response, reverse("catalog:worker-list"))
        worker = Worker.objects.get(username="anna")
        self.assertTrue(worker.check_password(PASSWORD))
        self.assertEqual(worker.position, self.position)

    def test_create_worker_with_different_passwords_is_rejected(self):
        response = self.client.post(
            reverse("catalog:worker-create"),
            self.build_creation_data(password2="Another123!"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Worker.objects.filter(username="anna").exists())

    def test_update_worker(self):
        worker = Worker.objects.create_user(username="anna", password=PASSWORD)
        response = self.client.post(
            reverse("catalog:worker-update", args=[worker.pk]),
            {
                "username": "anna",
                "first_name": "Anna",
                "last_name": "Smith",
                "email": "anna@example.com",
                "position": self.position.pk,
            },
        )
        self.assertRedirects(response, reverse("catalog:worker-list"))
        worker.refresh_from_db()
        self.assertEqual(worker.last_name, "Smith")
        self.assertEqual(worker.position, self.position)

    def test_delete_worker(self):
        worker = Worker.objects.create_user(username="anna", password=PASSWORD)
        response = self.client.post(reverse("catalog:worker-delete", args=[worker.pk]))
        self.assertRedirects(response, reverse("catalog:worker-list"))
        self.assertFalse(Worker.objects.filter(pk=worker.pk).exists())

    def test_worker_detail_splits_tasks_by_status(self):
        pending_task = self.create_task(name="Pending one")
        pending_task.assignees.add(self.worker)
        completed_task = self.create_task(name="Done one", is_completed=True)
        completed_task.assignees.add(self.worker)
        self.create_task(name="Not mine")
        response = self.client.get(
            reverse("catalog:worker-detail", args=[self.worker.pk]),
        )
        self.assertEqual(list(response.context["pending_tasks"]), [pending_task])
        self.assertEqual(list(response.context["completed_tasks"]), [completed_task])

    def test_create_worker_without_position_is_rejected(self):
        response = self.client.post(
            reverse("catalog:worker-create"),
            self.build_creation_data(position=""),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("position", response.context["form"].errors)
        self.assertFalse(Worker.objects.filter(username="anna").exists())

    def test_update_worker_without_position_is_rejected(self):
        worker = Worker.objects.create_user(
            username="anna",
            password=PASSWORD,
            position=self.position,
        )
        response = self.client.post(
            reverse("catalog:worker-update", args=[worker.pk]),
            {
                "username": "anna",
                "first_name": "Anna",
                "last_name": "Smith",
                "email": "anna@example.com",
                "position": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("position", response.context["form"].errors)
        worker.refresh_from_db()
        self.assertEqual(worker.position, self.position)


class TaskTypeCrudTests(LoggedInTestCase):
    def test_create_task_type(self):
        response = self.client.post(
            reverse("catalog:task-type-create"),
            {"name": "Refactoring"},
        )
        self.assertRedirects(response, reverse("catalog:task-type-list"))
        self.assertTrue(TaskType.objects.filter(name="Refactoring").exists())

    def test_duplicate_task_type_is_rejected(self):
        response = self.client.post(
            reverse("catalog:task-type-create"),
            {"name": "Bug"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(TaskType.objects.filter(name="Bug").count(), 1)

    def test_update_task_type(self):
        response = self.client.post(
            reverse("catalog:task-type-update", args=[self.task_type.pk]),
            {"name": "Defect"},
        )
        self.assertRedirects(response, reverse("catalog:task-type-list"))
        self.task_type.refresh_from_db()
        self.assertEqual(self.task_type.name, "Defect")

    def test_delete_unused_task_type(self):
        unused_type = TaskType.objects.create(name="Refactoring")
        response = self.client.post(
            reverse("catalog:task-type-delete", args=[unused_type.pk]),
        )
        self.assertRedirects(response, reverse("catalog:task-type-list"))
        self.assertFalse(TaskType.objects.filter(pk=unused_type.pk).exists())

    def test_delete_used_task_type_shows_message(self):
        self.create_task()
        response = self.client.post(
            reverse("catalog:task-type-delete", args=[self.task_type.pk]),
            follow=True,
        )
        self.assertContains(response, "still in use")
        self.assertTrue(TaskType.objects.filter(pk=self.task_type.pk).exists())


class PositionCrudTests(LoggedInTestCase):
    def test_create_position(self):
        response = self.client.post(
            reverse("catalog:position-create"),
            {"name": "DevOps"},
        )
        self.assertRedirects(response, reverse("catalog:position-list"))
        self.assertTrue(Position.objects.filter(name="DevOps").exists())

    def test_duplicate_position_is_rejected(self):
        response = self.client.post(
            reverse("catalog:position-create"),
            {"name": "Developer"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Position.objects.filter(name="Developer").count(), 1)

    def test_update_position(self):
        response = self.client.post(
            reverse("catalog:position-update", args=[self.position.pk]),
            {"name": "Backend developer"},
        )
        self.assertRedirects(response, reverse("catalog:position-list"))
        self.position.refresh_from_db()
        self.assertEqual(self.position.name, "Backend developer")

    def test_delete_unused_position(self):
        unused_position = Position.objects.create(name="QA")
        response = self.client.post(
            reverse("catalog:position-delete", args=[unused_position.pk]),
        )
        self.assertRedirects(response, reverse("catalog:position-list"))
        self.assertFalse(Position.objects.filter(pk=unused_position.pk).exists())

    def test_delete_used_position_shows_message_and_keeps_worker(self):
        response = self.client.post(
            reverse("catalog:position-delete", args=[self.position.pk]),
            follow=True,
        )
        self.assertContains(response, "still in use")
        self.assertTrue(Position.objects.filter(pk=self.position.pk).exists())
        self.assertTrue(Worker.objects.filter(pk=self.worker.pk).exists())
