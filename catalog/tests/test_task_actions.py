from django.urls import reverse

from catalog.tests.base import LoggedInTestCase


class TaskActionTestCase(LoggedInTestCase):
    def setUp(self):
        super().setUp()
        self.task = self.create_task()
        self.detail_url = reverse("catalog:task-detail", args=[self.task.pk])

    def post(self, url_name):
        return self.client.post(reverse(url_name, args=[self.task.pk]))


class AssignmentTests(TaskActionTestCase):
    def test_assign_me(self):
        response = self.post("catalog:task-assign")
        self.assertRedirects(response, self.detail_url)
        self.assertIn(self.worker, self.task.assignees.all())

    def test_assign_me_twice_keeps_single_assignment(self):
        self.post("catalog:task-assign")
        self.post("catalog:task-assign")
        self.assertEqual(self.task.assignees.count(), 1)

    def test_unassign_me(self):
        self.task.assignees.add(self.worker)
        self.post("catalog:task-unassign")
        self.assertNotIn(self.worker, self.task.assignees.all())

    def test_unassign_when_not_assigned_does_nothing(self):
        response = self.post("catalog:task-unassign")
        self.assertRedirects(response, self.detail_url)
        self.assertEqual(self.task.assignees.count(), 0)

    def test_button_text_depends_on_assignment(self):
        response = self.client.get(self.detail_url)
        self.assertContains(response, "Assign me to this task")
        self.task.assignees.add(self.worker)
        response = self.client.get(self.detail_url)
        self.assertContains(response, "Remove me from this task")

    def test_actions_require_post(self):
        for url_name in ("catalog:task-assign", "catalog:task-unassign"):
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name, args=[self.task.pk]))
                self.assertEqual(response.status_code, 405)

    def test_unknown_task_returns_404(self):
        response = self.client.post(reverse("catalog:task-assign", args=[9999]))
        self.assertEqual(response.status_code, 404)


class CompletionTests(TaskActionTestCase):
    def test_complete_task(self):
        response = self.post("catalog:task-complete")
        self.assertRedirects(response, self.detail_url)
        self.task.refresh_from_db()
        self.assertTrue(self.task.is_completed)

    def test_complete_twice_stays_completed(self):
        self.post("catalog:task-complete")
        self.post("catalog:task-complete")
        self.task.refresh_from_db()
        self.assertTrue(self.task.is_completed)

    def test_reopen_task(self):
        self.task.is_completed = True
        self.task.save()
        self.post("catalog:task-reopen")
        self.task.refresh_from_db()
        self.assertFalse(self.task.is_completed)

    def test_reopen_open_task_stays_open(self):
        self.post("catalog:task-reopen")
        self.task.refresh_from_db()
        self.assertFalse(self.task.is_completed)

    def test_button_text_depends_on_status(self):
        response = self.client.get(self.detail_url)
        self.assertContains(response, "Mark as completed")
        self.task.is_completed = True
        self.task.save()
        response = self.client.get(self.detail_url)
        self.assertContains(response, "Mark as not completed")

    def test_actions_require_post(self):
        for url_name in ("catalog:task-complete", "catalog:task-reopen"):
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name, args=[self.task.pk]))
                self.assertEqual(response.status_code, 405)
