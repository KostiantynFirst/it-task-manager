from datetime import timedelta
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from catalog.models import Position, Task, TaskType, Worker
from catalog.tests.base import PASSWORD, LoggedInTestCase


class TaskSearchAndFilterTests(LoggedInTestCase):
    def setUp(self):
        super().setUp()
        self.login_task = self.create_task(
            name="Fix login page",
            priority=Task.Priority.URGENT,
        )
        self.button_task = self.create_task(
            name="Add Google button",
            priority=Task.Priority.LOW,
            is_completed=True,
        )
        self.url = reverse("catalog:task-list")

    def get_tasks(self, **params):
        response = self.client.get(self.url, params)
        return list(response.context["task_list"])

    def test_list_without_filters_shows_all_tasks(self):
        self.assertCountEqual(
            self.get_tasks(),
            [self.login_task, self.button_task],
        )

    def test_search_by_name(self):
        self.assertEqual(self.get_tasks(name="login"), [self.login_task])

    def test_combined_search_and_filter(self):
        self.assertEqual(self.get_tasks(name="Google", status="pending"), [])

    def test_search_form_keeps_entered_value(self):
        response = self.client.get(self.url, {"name": "login"})
        self.assertEqual(response.context["search_form"]["name"].value(), "login")

    def test_priority_badges_are_shown(self):
        response = self.client.get(self.url)
        self.assertContains(response, "text-bg-danger")
        self.assertContains(response, "text-bg-secondary")

    def test_overdue_task_is_highlighted(self):
        self.create_task(
            name="Old task",
            deadline=self.today - timedelta(days=30),
        )
        response = self.client.get(self.url)
        self.assertContains(response, "table-danger")
        self.assertContains(response, "Overdue")

    def test_task_with_future_deadline_is_not_highlighted(self):
        response = self.client.get(self.url)
        self.assertNotContains(response, "table-danger")
        self.assertNotContains(response, "Overdue")


class TaskListQueryTests(LoggedInTestCase):
    def test_query_count_does_not_grow_with_number_of_tasks(self):
        url = reverse("catalog:task-list")
        self.create_task(name="First")
        with CaptureQueriesContext(connection) as few_queries:
            self.client.get(url)
        for index in range(4):
            task = self.create_task(name=f"Extra {index}")
            task.assignees.add(self.worker)
        with CaptureQueriesContext(connection) as many_queries:
            self.client.get(url)
        self.assertEqual(len(few_queries), len(many_queries))


class TaskPaginationTests(LoggedInTestCase):
    def setUp(self):
        super().setUp()
        for index in range(7):
            self.create_task(name=f"Task {index}")
        self.url = reverse("catalog:task-list")

    def test_first_page_has_five_tasks(self):
        response = self.client.get(self.url)
        self.assertTrue(response.context["is_paginated"])
        self.assertEqual(len(response.context["task_list"]), 5)

    def test_second_page_has_remaining_tasks(self):
        response = self.client.get(self.url, {"page": 2})
        self.assertEqual(len(response.context["task_list"]), 2)

    def test_page_out_of_range_returns_404(self):
        response = self.client.get(self.url, {"page": 999})
        self.assertEqual(response.status_code, 404)

    def test_search_parameters_are_kept_in_pagination_links(self):
        response = self.client.get(self.url, {"name": "Task"})
        self.assertEqual(response.context["query_string"], "name=Task")
        self.assertContains(response, "name=Task&page=2")

    def test_page_parameter_is_not_duplicated_in_query_string(self):
        response = self.client.get(self.url, {"name": "Task", "page": 2})
        self.assertEqual(response.context["query_string"], "name=Task")


class WorkerListTests(LoggedInTestCase):
    def setUp(self):
        super().setUp()
        self.anna = Worker.objects.create_user(username="anna", password=PASSWORD)
        self.url = reverse("catalog:worker-list")

    def test_search_by_username(self):
        response = self.client.get(self.url, {"username": "ann"})
        self.assertEqual(list(response.context["worker_list"]), [self.anna])

    def test_search_without_matches_shows_message(self):
        response = self.client.get(self.url, {"username": "nobody"})
        self.assertContains(response, "No workers found.")

    def test_pagination(self):
        for index in range(4):
            Worker.objects.create_user(username=f"user{index}", password=PASSWORD)
        response = self.client.get(self.url)
        self.assertEqual(len(response.context["worker_list"]), 5)
        response = self.client.get(self.url, {"page": 2})
        self.assertEqual(len(response.context["worker_list"]), 1)


class TaskTypeAndPositionListTests(LoggedInTestCase):
    def test_search_task_types_by_name(self):
        refactoring = TaskType.objects.create(name="Refactoring")
        response = self.client.get(
            reverse("catalog:task-type-list"),
            {"name": "refac"},
        )
        self.assertEqual(list(response.context["tasktype_list"]), [refactoring])

    def test_search_positions_by_name(self):
        devops = Position.objects.create(name="DevOps")
        response = self.client.get(
            reverse("catalog:position-list"),
            {"name": "devo"},
        )
        self.assertEqual(list(response.context["position_list"]), [devops])
