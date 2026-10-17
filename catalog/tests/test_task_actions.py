from django.urls import reverse

from catalog.tests.base import LoggedInTestCase


class AssignmentTests(LoggedInTestCase):
    def setUp(self):
        super().setUp()
        self.task = self.create_task()
        self.assign_url = reverse("catalog:task-toggle-assign", args=[self.task.pk])
        self.detail_url = reverse("catalog:task-detail", args=[self.task.pk])

    def test_assign_me(self):
        response = self.client.post(self.assign_url)
        self.assertRedirects(response, self.detail_url)
        self.assertIn(self.worker, self.task.assignees.all())

    def test_remove_me(self):
        self.task.assignees.add(self.worker)
        self.client.post(self.assign_url)
        self.assertNotIn(self.worker, self.task.assignees.all())

    def test_button_text_depends_on_assignment(self):
        response = self.client.get(self.detail_url)
        self.assertFalse(response.context["is_assigned"])
        self.assertContains(response, "Assign me to this task")
        self.task.assignees.add(self.worker)
        response = self.client.get(self.detail_url)
        self.assertTrue(response.context["is_assigned"])
        self.assertContains(response, "Remove me from this task")

    def test_assign_requires_post(self):
        response = self.client.get(self.assign_url)
        self.assertEqual(response.status_code, 405)

    def test_assign_unknown_task_returns_404(self):
        response = self.client.post(
            reverse("catalog:task-toggle-assign", args=[9999]),
        )
        self.assertEqual(response.status_code, 404)


class CompletionToggleTests(LoggedInTestCase):
    def setUp(self):
        super().setUp()
        self.task = self.create_task()
        self.toggle_url = reverse("catalog:task-toggle-complete", args=[self.task.pk])

    def test_mark_as_completed(self):
        response = self.client.post(self.toggle_url)
        self.assertRedirects(
            response,
            reverse("catalog:task-detail", args=[self.task.pk]),
        )
        self.task.refresh_from_db()
        self.assertTrue(self.task.is_completed)

    def test_mark_as_not_completed(self):
        self.task.is_completed = True
        self.task.save()
        self.client.post(self.toggle_url)
        self.task.refresh_from_db()
        self.assertFalse(self.task.is_completed)

    def test_toggle_requires_post(self):
        response = self.client.get(self.toggle_url)
        self.assertEqual(response.status_code, 405)
        self.task.refresh_from_db()
        self.assertFalse(self.task.is_completed)
