"""
DRF 序列化器
"""
from rest_framework import serializers
from .models import TaskModule, TaskItem, Customer, Project


class TaskItemSerializer(serializers.ModelSerializer):
    """任务项序列化器"""
    class Meta:
        model = TaskItem
        fields = '__all__'
        read_only_fields = ['created_at']

    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError('任务内容不能为空')
        return value


class TaskModuleSerializer(serializers.ModelSerializer):
    """任务模块序列化器，包含关联的任务项统计"""
    today_count = serializers.SerializerMethodField()
    todo_count = serializers.SerializerMethodField()

    class Meta:
        model = TaskModule
        fields = ['id', 'name', 'created_at', 'today_count', 'todo_count']
        read_only_fields = ['created_at']

    def get_today_count(self, obj):
        return obj.tasks.filter(task_type='today').count()

    def get_todo_count(self, obj):
        return obj.tasks.filter(task_type='todo').count()


class CustomerSerializer(serializers.ModelSerializer):
    """客户序列化器"""
    project_count = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = ['id', 'name', 'created_at', 'project_count']
        read_only_fields = ['created_at']

    def get_project_count(self, obj):
        return obj.projects.count()


class ProjectSerializer(serializers.ModelSerializer):
    """项目配置序列化器"""
    customer_name = serializers.CharField(source='customer.name', read_only=True)

    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ['serial_number']

    def validate_project_name(self, value):
        if not value.strip():
            raise serializers.ValidationError('项目名称不能为空')
        return value
