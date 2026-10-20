from django.urls import reverse

from catalog.tests.base import PASSWORD, BaseTestCase, LoggedInTestCase


class AnonymousAccessTests(BaseTestCase):
    def test_login_page_is_public(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)

    def test_protected_pages_redirect_to_login(self):
        task = self.create_task()
        urls = [
            reverse("catalog:index"),
            reverse("catalog:task-list"),
            reverse("catalog:task-create"),
            reverse("catalog:task-detail", args=[task.pk]),
            reverse("catalog:task-update", args=[task.pk]),
            reverse("catalog:task-delete", args=[task.pk]),
            reverse("catalog:worker-list"),
            reverse("catalog:worker-create"),
            reverse("catalog:worker-detail", args=[self.worker.pk]),
            reverse("catalog:task-type-list"),
            reverse("catalog:position-list"),
        ]
        login_url = reverse("login")
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(response, f"{login_url}?next={url}")

    def test_task_actions_require_login(self):
        task = self.create_task()
        for url_name in ("catalog:task-assign", "catalog:task-complete"):
            with self.subTest(url_name=url_name):
                response = self.client.post(reverse(url_name, args=[task.pk]))
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith(reverse("login")))
        task.refresh_from_db()
        self.assertFalse(task.is_completed)
        self.assertEqual(task.assignees.count(), 0)

    def test_login_with_valid_credentials(self):
        response = self.client.post(
            reverse("login"),
            {"username": "john", "password": PASSWORD},
        )
        self.assertRedirects(response, reverse("catalog:index"))

    def test_login_with_wrong_password(self):
        response = self.client.post(
            reverse("login"),
            {"username": "john", "password": "wrong-password"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)


class AuthenticatedAccessTests(LoggedInTestCase):
    def test_pages_are_available(self):
        task = self.create_task()
        urls = [
            reverse("catalog:index"),
            reverse("catalog:task-list"),
            reverse("catalog:task-create"),
            reverse("catalog:task-detail", args=[task.pk]),
            reverse("catalog:task-update", args=[task.pk]),
            reverse("catalog:task-delete", args=[task.pk]),
            reverse("catalog:worker-list"),
            reverse("catalog:worker-create"),
            reverse("catalog:worker-detail", args=[self.worker.pk]),
            reverse("catalog:worker-update", args=[self.worker.pk]),
            reverse("catalog:worker-delete", args=[self.worker.pk]),
            reverse("catalog:task-type-list"),
            reverse("catalog:task-type-create"),
            reverse("catalog:task-type-update", args=[self.task_type.pk]),
            reverse("catalog:task-type-delete", args=[self.task_type.pk]),
            reverse("catalog:position-list"),
            reverse("catalog:position-create"),
            reverse("catalog:position-update", args=[self.position.pk]),
            reverse("catalog:position-delete", args=[self.position.pk]),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_index_counters(self):
        self.create_task(name="Done", is_completed=True)
        self.create_task(name="Open")
        response = self.client.get(reverse("catalog:index"))
        self.assertEqual(response.context["num_workers"], 1)
        self.assertEqual(response.context["num_tasks"], 2)
        self.assertEqual(response.context["num_completed"], 1)
        self.assertEqual(response.context["num_pending"], 1)

    def test_visit_counter_is_stored_in_session(self):
        index_url = reverse("catalog:index")
        self.client.get(index_url)
        response = self.client.get(index_url)
        self.assertEqual(response.context["num_visits"], 2)

    def test_logout(self):
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("login"))
        response = self.client.get(reverse("catalog:index"))
        self.assertEqual(response.status_code, 302)
