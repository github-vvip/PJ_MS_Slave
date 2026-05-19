"""
Django Admin 注册
"""
from django.contrib import admin
from .models import TaskModule, TaskItem, Customer, Project


@admin.register(TaskModule)
class TaskModuleAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'created_at']
    search_fields = ['name']


@admin.register(TaskItem)
class TaskItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'module', 'task_type', 'content', 'order', 'is_completed', 'postpone_tomorrow', 'created_at']
    list_filter = ['task_type', 'is_completed', 'postpone_tomorrow']
    search_fields = ['content']


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'created_at']
    search_fields = ['name']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['serial_number', 'customer', 'project_name', 'hardware_version', 'brand', 'model', 'android_version']
    list_filter = ['customer']
    search_fields = ['project_name', 'hardware_version', 'brand', 'model']
