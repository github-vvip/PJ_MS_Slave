"""
API URL 路由配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import TaskModuleViewSet, TaskItemViewSet, CustomerViewSet, ProjectViewSet, HistorySnapshotViewSet, search_projects

router = DefaultRouter()
router.register(r'task-modules', TaskModuleViewSet)
router.register(r'task-items', TaskItemViewSet)
router.register(r'customers', CustomerViewSet)
router.register(r'projects', ProjectViewSet)
router.register(r'history-snapshots', HistorySnapshotViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('search/', search_projects, name='project-search'),
]
