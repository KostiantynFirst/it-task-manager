from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from catalog.models import Position, Task, TaskType, Worker

PASSWORD = "StrongPass123!"


class BaseTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.position = Position.objects.create(name="Developer")
        cls.task_type = TaskType.objects.create(name="Bug")
        cls.worker = Worker.objects.create_user(
            username="john",
            password=PASSWORD,
            first_name="John",
            last_name="Doe",
            position=cls.position,
            is_staff=True,
        )
        cls.today = timezone.localdate()

    def create_task(self, name="Fix bug", **fields):
        defaults = {
            "description": "Some description",
            "deadline": self.today + timedelta(days=1),
            "task_type": self.task_type,
        }
        defaults.update(fields)
        return Task.objects.create(name=name, **defaults)


class LoggedInTestCase(BaseTestCase):
    def setUp(self):
        self.client.force_login(self.worker)
