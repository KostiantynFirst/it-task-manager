from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from catalog.models import Position, Task, TaskType, Worker

DEMO_PASSWORD = "demo12345"

POSITIONS = ["Developer", "Project Manager", "QA", "Designer", "DevOps"]

TASK_TYPES = ["Bug", "New feature", "Breaking change", "Refactoring", "QA"]

WORKERS = [
    {
        "username": "alice",
        "first_name": "Alice",
        "last_name": "Johnson",
        "position": "Project Manager",
    },
    {
        "username": "bob",
        "first_name": "Bob",
        "last_name": "Miller",
        "position": "Developer",
    },
    {
        "username": "carol",
        "first_name": "Carol",
        "last_name": "Davis",
        "position": "QA",
    },
    {
        "username": "dave",
        "first_name": "Dave",
        "last_name": "Wilson",
        "position": "DevOps",
    },
    {
        "username": "eve",
        "first_name": "Eve",
        "last_name": "Taylor",
        "position": "Designer",
    },
]

ADMIN = {
    "username": "admin",
    "first_name": "Admin",
    "last_name": "User",
    "position": "Project Manager",
}

# days_left: deadline relative to today (negative means already overdue)
TASKS = [
    {
        "name": "Fix Dashboard for Vacancies",
        "description": "Vacancy counters on the dashboard show wrong numbers.",
        "priority": Task.Priority.URGENT,
        "task_type": "Bug",
        "days_left": -2,
        "is_completed": False,
        "assignees": ["bob", "carol"],
    },
    {
        "name": "Fix login redirect loop",
        "description": "Users are redirected back to the login page after signing in.",
        "priority": Task.Priority.URGENT,
        "task_type": "Bug",
        "days_left": 0,
        "is_completed": False,
        "assignees": ["bob"],
    },
    {
        "name": "Add sign-in with Google button",
        "description": "Add a Google OAuth button to the login page.",
        "priority": Task.Priority.HIGH,
        "task_type": "New feature",
        "days_left": 5,
        "is_completed": False,
        "assignees": ["bob"],
    },
    {
        "name": "Migrate API to v2",
        "description": "Move all public endpoints to the new API version.",
        "priority": Task.Priority.HIGH,
        "task_type": "Breaking change",
        "days_left": 14,
        "is_completed": False,
        "assignees": ["bob", "dave"],
    },
    {
        "name": "Refactor payment module",
        "description": "Split the payment module into smaller services.",
        "priority": Task.Priority.MEDIUM,
        "task_type": "Refactoring",
        "days_left": 10,
        "is_completed": False,
        "assignees": ["dave"],
    },
    {
        "name": "Write regression tests for checkout",
        "description": "Cover the checkout flow with automated regression tests.",
        "priority": Task.Priority.MEDIUM,
        "task_type": "QA",
        "days_left": 3,
        "is_completed": False,
        "assignees": ["carol"],
    },
    {
        "name": "Audit database indexes",
        "description": "Find slow queries and add the missing indexes.",
        "priority": Task.Priority.MEDIUM,
        "task_type": "Refactoring",
        "days_left": -3,
        "is_completed": False,
        "assignees": ["dave", "bob"],
    },
    {
        "name": "Redesign onboarding screens",
        "description": "Prepare new mockups for the onboarding flow.",
        "priority": Task.Priority.LOW,
        "task_type": "New feature",
        "days_left": 21,
        "is_completed": False,
        "assignees": ["eve"],
    },
    {
        "name": "Set up CI pipeline",
        "description": "Run linters and tests on every push.",
        "priority": Task.Priority.HIGH,
        "task_type": "New feature",
        "days_left": -10,
        "is_completed": True,
        "assignees": ["dave"],
    },
    {
        "name": "Fix typo on pricing page",
        "description": "The plan name is misspelled in the pricing table.",
        "priority": Task.Priority.LOW,
        "task_type": "Bug",
        "days_left": -7,
        "is_completed": True,
        "assignees": ["eve", "alice"],
    },
]


class Command(BaseCommand):
    help = "Load demo positions, task types, workers and tasks."

    def handle(self, *_args, **_options):
        positions = self.create_positions()
        task_types = self.create_task_types()
        workers = self.create_workers(positions)
        self.create_tasks(task_types, workers)
        self.stdout.write(self.style.SUCCESS("Demo data loaded."))
        self.stdout.write(f"Demo password for all accounts: {DEMO_PASSWORD}")

    @staticmethod
    def create_positions():
        return {
            name: Position.objects.get_or_create(name=name)[0]
            for name in POSITIONS
        }

    @staticmethod
    def create_task_types():
        return {
            name: TaskType.objects.get_or_create(name=name)[0]
            for name in TASK_TYPES
        }

    @staticmethod
    def create_workers(positions):
        workers = {}
        for worker_spec in [ADMIN] + WORKERS:
            username = worker_spec["username"]
            worker, created = Worker.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": worker_spec["first_name"],
                    "last_name": worker_spec["last_name"],
                    "email": f"{username}@example.com",
                    "position": positions[worker_spec["position"]],
                },
            )
            if created:
                worker.set_password(DEMO_PASSWORD)
                if worker_spec is ADMIN:
                    worker.is_staff = True
                    worker.is_superuser = True
                worker.save()
            workers[username] = worker
        return workers

    @staticmethod
    def create_tasks(task_types, workers):
        today = timezone.localdate()
        for task_spec in TASKS:
            task, created = Task.objects.get_or_create(
                name=task_spec["name"],
                defaults={
                    "description": task_spec["description"],
                    "deadline": today + timedelta(days=task_spec["days_left"]),
                    "priority": task_spec["priority"],
                    "is_completed": task_spec["is_completed"],
                    "task_type": task_types[task_spec["task_type"]],
                },
            )
            if created:
                task.assignees.set(
                    [workers[username] for username in task_spec["assignees"]]
                )