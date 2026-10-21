from django.urls import reverse

from catalog.models import Task, Worker
from catalog.tests.base import PASSWORD, BaseTestCase, LoggedInTestCase


class MemberPermissionTests(BaseTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.member = Worker.objects.create_user(
            username="member",
            password=PASSWORD,
            position=cls.position,
        )

    def setUp(self):
        self.client.force_login(self.member)
        self.task = self.create_task()

    def test_member_cannot_open_staff_only_pages(self):
        urls = [
            reverse("catalog:worker-create"),
            reverse("catalog:worker-update", args=[self.worker.pk]),
            reverse("catalog:worker-delete", args=[self.worker.pk]),
            reverse("catalog:task-type-create"),
            reverse("catalog:task-type-update", args=[self.task_type.pk]),
            reverse("catalog:task-type-delete", args=[self.task_type.pk]),
            reverse("catalog:position-create"),
            reverse("catalog:position-update", args=[self.position.pk]),
            reverse("catalog:position-delete", args=[self.position.pk]),
            reverse("catalog:task-delete", args=[self.task.pk]),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)

    def test_member_cannot_delete_task(self):
        self.client.post(reverse("catalog:task-delete", args=[self.task.pk]))
        self.assertTrue(Task.objects.filter(pk=self.task.pk).exists())

    def test_member_can_create_task(self):
        response = self.client.get(reverse("catalog:task-create"))
        self.assertEqual(response.status_code, 200)

    def test_member_cannot_edit_or_complete_unassigned_task(self):
        for url_name in ("catalog:task-update", "catalog:task-complete"):
            with self.subTest(url_name=url_name):
                url = reverse(url_name, args=[self.task.pk])
                self.assertEqual(self.client.post(url).status_code, 403)
        self.task.refresh_from_db()
        self.assertFalse(self.task.is_completed)

    def test_member_can_edit_and_complete_assigned_task(self):
        self.task.assignees.add(self.member)
        response = self.client.get(reverse("catalog:task-update", args=[self.task.pk]))
        self.assertEqual(response.status_code, 200)
        self.client.post(reverse("catalog:task-complete", args=[self.task.pk]))
        self.task.refresh_from_db()
        self.assertTrue(self.task.is_completed)

    def test_member_can_assign_self(self):
        self.client.post(reverse("catalog:task-assign", args=[self.task.pk]))
        self.assertIn(self.member, self.task.assignees.all())

    def test_member_can_edit_only_own_profile(self):
        own_url = reverse("catalog:worker-update", args=[self.member.pk])
        other_url = reverse("catalog:worker-update", args=[self.worker.pk])
        self.assertEqual(self.client.get(own_url).status_code, 200)
        self.assertEqual(self.client.get(other_url).status_code, 403)

    def test_member_does_not_see_manage_buttons(self):
        response = self.client.get(reverse("catalog:task-detail", args=[self.task.pk]))
        self.assertNotContains(response, "Delete")
        self.assertNotContains(response, "Mark as completed")

    def test_member_does_not_see_create_buttons(self):
        response = self.client.get(reverse("catalog:position-list"))
        self.assertNotContains(response, "New position")

    def test_member_does_not_see_edit_and_delete_links_in_lists(self):
        cases = (
            ("catalog:position-list", "position", self.position),
            ("catalog:task-type-list", "task-type", self.task_type),
        )
        for list_url_name, prefix, obj in cases:
            with self.subTest(list_url_name=list_url_name):
                response = self.client.get(reverse(list_url_name))
                self.assertNotContains(
                    response, reverse(f"catalog:{prefix}-update", args=[obj.pk])
                )
                self.assertNotContains(
                    response, reverse(f"catalog:{prefix}-delete", args=[obj.pk])
                )


class StaffInterfaceTests(LoggedInTestCase):
    def test_staff_sees_manage_buttons(self):
        task = self.create_task()
        response = self.client.get(reverse("catalog:task-detail", args=[task.pk]))
        self.assertContains(response, "Delete")
        self.assertContains(response, "Mark as completed")

    def test_staff_sees_create_buttons(self):
        response = self.client.get(reverse("catalog:position-list"))
        self.assertContains(response, "New position")

    def test_staff_sees_edit_and_delete_links_in_lists(self):
        cases = (
            ("catalog:position-list", "position", self.position),
            ("catalog:task-type-list", "task-type", self.task_type),
        )
        for list_url_name, prefix, obj in cases:
            with self.subTest(list_url_name=list_url_name):
                response = self.client.get(reverse(list_url_name))
                self.assertContains(
                    response, reverse(f"catalog:{prefix}-update", args=[obj.pk])
                )
                self.assertContains(
                    response, reverse(f"catalog:{prefix}-delete", args=[obj.pk])
                )
