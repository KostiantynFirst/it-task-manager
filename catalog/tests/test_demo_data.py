from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from catalog.management.commands.load_demo_data import DEMO_PASSWORD
from catalog.models import Position, Task, TaskType, Worker


class LoadDemoDataTests(TestCase):
    @staticmethod
    def run_command():
        call_command("load_demo_data", stdout=StringIO())

    def test_creates_demo_data(self):
        self.run_command()
        self.assertEqual(Position.objects.count(), 5)
        self.assertEqual(TaskType.objects.count(), 5)
        self.assertEqual(Worker.objects.count(), 6)
        self.assertEqual(Task.objects.count(), 10)
        self.assertTrue(Task.objects.filter(is_completed=True).exists())
        self.assertTrue(any(task.is_overdue for task in Task.objects.all()))

    def test_command_is_idempotent(self):
        self.run_command()
        self.run_command()
        self.assertEqual(Worker.objects.count(), 6)
        self.assertEqual(Task.objects.count(), 10)

    def test_demo_worker_can_log_in(self):
        self.run_command()
        self.assertTrue(
            self.client.login(username="alice", password=DEMO_PASSWORD)
        )

    def test_admin_is_superuser(self):
        self.run_command()
        self.assertTrue(Worker.objects.get(username="admin").is_superuser)
