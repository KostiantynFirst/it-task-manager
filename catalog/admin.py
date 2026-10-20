from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from catalog.models import Position, TaskType, Worker, Task


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(TaskType)
class TaskTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Worker)
class WorkerAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ("position",)
    list_filter = UserAdmin.list_display + ("position",)
    fieldsets = UserAdmin.fieldsets + (
        ("Additional info", {"fields": ("position",)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Additional info", {"fields": ("first_name", "last_name", "position",)}),
    )


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "task_type",
        "priority",
        "deadline",
        "is_completed"
    )
    list_filter = (
        "is_completed",
        "priority",
        "task_type"
    )
    search_fields = ("name", "description")
    filter_horizontal = ("assignees",)
