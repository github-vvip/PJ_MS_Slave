"""
DRF 视图集
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Max, Q
from .models import TaskModule, TaskItem, Customer, Project, HistorySnapshot
from .serializers import TaskModuleSerializer, TaskItemSerializer, CustomerSerializer, ProjectSerializer, HistorySnapshotSerializer


class TaskModuleViewSet(viewsets.ModelViewSet):
    """任务模块视图集：支持 CRUD"""
    queryset = TaskModule.objects.all()
    serializer_class = TaskModuleSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'message': '删除成功'}, status=status.HTTP_200_OK)

    def perform_destroy(self, instance):
        instance.delete()


class TaskItemViewSet(viewsets.ModelViewSet):
    """任务项视图集：支持 CRUD 及自定义操作"""
    queryset = TaskItem.objects.all()
    serializer_class = TaskItemSerializer

    def get_queryset(self):
        queryset = TaskItem.objects.all()
        module_id = self.request.query_params.get('module')
        task_type = self.request.query_params.get('task_type')
        if module_id:
            queryset = queryset.filter(module_id=module_id)
        if task_type:
            queryset = queryset.filter(task_type=task_type)
        if task_type == 'today':
            queryset = queryset.order_by('order', '-created_at')
        else:
            queryset = queryset.order_by('-created_at')
        return queryset

    @action(detail=True, methods=['post'], url_path='move-to-todo')
    def move_to_todo(self, request, pk=None):
        task = self.get_object()
        task.task_type = 'todo'
        task.order = 0
        task.save()
        serializer = self.get_serializer(task)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='move-to-today')
    def move_to_today(self, request, pk=None):
        task = self.get_object()
        max_order = TaskItem.objects.filter(
            module_id=task.module_id, task_type='today'
        ).aggregate(max_order=Max('order'))['max_order'] or 0
        task.task_type = 'today'
        task.order = max_order + 1
        task.postpone_tomorrow = False
        task.save()
        serializer = self.get_serializer(task)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='postpone-tomorrow')
    def postpone_tomorrow(self, request, pk=None):
        task = self.get_object()
        task.postpone_tomorrow = True
        task.save()
        serializer = self.get_serializer(task)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='cancel-postpone')
    def cancel_postpone(self, request, pk=None):
        task = self.get_object()
        task.postpone_tomorrow = False
        task.save()
        serializer = self.get_serializer(task)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='toggle-complete')
    def toggle_complete(self, request, pk=None):
        task = self.get_object()
        task.is_completed = not task.is_completed
        task.save()
        serializer = self.get_serializer(task)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='batch-reorder')
    def batch_reorder(self, request):
        items = request.data.get('items', [])
        for item_data in items:
            TaskItem.objects.filter(id=item_data.get('id')).update(order=item_data.get('order', 0))
        return Response({'message': '排序更新成功'})

    @action(detail=False, methods=['post'], url_path='check-postpone')
    def check_postpone(self, request):
        from django.utils import timezone
        today = timezone.now().date()
        postponed_tasks = TaskItem.objects.filter(
            task_type='todo', postpone_tomorrow=True
        )
        moved_count = 0
        for task in postponed_tasks:
            created_date = task.created_at.date() if task.created_at else today
            if created_date < today:
                max_order = TaskItem.objects.filter(
                    module_id=task.module_id, task_type='today'
                ).aggregate(max_order=Max('order'))['max_order'] or 0
                task.task_type = 'today'
                task.order = max_order + 1
                task.postpone_tomorrow = False
                task.save()
                moved_count += 1
        return Response({'message': f'已将 {moved_count} 条推迟任务转为今日任务'})


class CustomerViewSet(viewsets.ModelViewSet):
    """客户视图集：支持 CRUD"""
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'message': '删除成功'}, status=status.HTTP_200_OK)


class ProjectViewSet(viewsets.ModelViewSet):
    """项目配置视图集：按客户分组，支持 CRUD、筛选、导出"""
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def get_queryset(self):
        queryset = Project.objects.all()
        customer_id = self.request.query_params.get('customer')
        search = self.request.query_params.get('search')
        hardware_version = self.request.query_params.get('hardware_version')
        android_version = self.request.query_params.get('android_version')
        brand = self.request.query_params.get('brand')
        wifi = self.request.query_params.get('wifi')
        screen_size = self.request.query_params.get('screen_size')
        tp = self.request.query_params.get('tp')

        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        if search:
            queryset = queryset.filter(
                Q(project_name__icontains=search)
                | Q(hardware_version__icontains=search)
                | Q(brand__icontains=search)
                | Q(model__icontains=search)
            )
        if hardware_version:
            hv_list = hardware_version.split(',')
            queryset = queryset.filter(hardware_version__in=hv_list)
        if android_version:
            av_list = android_version.split(',')
            queryset = queryset.filter(android_version__in=av_list)
        if brand:
            queryset = queryset.filter(brand=brand)
        if wifi:
            queryset = queryset.filter(wifi=wifi)
        if screen_size:
            queryset = queryset.filter(screen_size=screen_size)
        if tp:
            queryset = queryset.filter(tp=tp)

        return queryset

    def perform_create(self, serializer):
        """新增时自动分配该客户内的序号"""
        customer = serializer.validated_data['customer']
        max_sn = Project.objects.filter(customer=customer).aggregate(max_sn=Max('serial_number'))['max_sn'] or 0
        serializer.save(serial_number=max_sn + 1)

    def destroy(self, request, *args, **kwargs):
        """删除后仅当前客户内序号自动递减补位"""
        instance = self.get_object()
        deleted_sn = instance.serial_number
        customer = instance.customer
        instance.delete()
        projects = Project.objects.filter(
            customer=customer, serial_number__gt=deleted_sn
        ).order_by('serial_number')
        for p in projects:
            p.serial_number -= 1
            p.save()
        return Response({'message': '删除成功'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='batch-import')
    def batch_import(self, request):
        """批量导入项目数据"""
        customer_id = request.data.get('customer_id')
        items = request.data.get('items', [])

        if not customer_id:
            return Response({'error': '请选择客户'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            return Response({'error': '客户不存在'}, status=status.HTTP_400_BAD_REQUEST)

        if not items:
            return Response({'error': '无有效数据'}, status=status.HTTP_400_BAD_REQUEST)

        created_count = 0
        updated_count = 0
        skipped_count = 0
        errors = []

        for idx, item in enumerate(items):
            project_name = item.get('project_name', '').strip()
            if not project_name:
                skipped_count += 1
                errors.append(f'第{idx + 1}行：项目名称为空，已跳过')
                continue

            hardware_version = (item.get('hardware_version') or '').strip()
            existing = Project.objects.filter(
                customer=customer, project_name=project_name, hardware_version=hardware_version
            ).first()

            if existing:
                overwrite = item.get('_overwrite', False)
                if overwrite:
                    for field, value in item.items():
                        if field in ('project_name', '_overwrite', 'serial_number'):
                            continue
                        if hasattr(existing, field):
                            setattr(existing, field, value)
                    existing.save()
                    updated_count += 1
                else:
                    skipped_count += 1
                    errors.append(f'项目名称【{project_name}】已存在，已跳过')
            else:
                max_sn = Project.objects.filter(customer=customer).aggregate(
                    max_sn=Max('serial_number')
                )['max_sn'] or 0
                project_data = {k: v for k, v in item.items() if k != '_overwrite'}
                project_data['customer'] = customer
                project_data['serial_number'] = max_sn + 1
                Project.objects.create(**project_data)
                created_count += 1

        return Response({
            'created': created_count,
            'updated': updated_count,
            'skipped': skipped_count,
            'errors': errors,
        })

    @action(detail=False, methods=['get'], url_path='filter-options')
    def filter_options(self, request):
        """获取筛选选项，可按客户过滤"""
        customer_id = request.query_params.get('customer')
        qs = Project.objects.all()
        if customer_id:
            qs = qs.filter(customer_id=customer_id)
        hardware_versions = list(qs.values_list('hardware_version', flat=True).exclude(hardware_version='').distinct())
        android_versions = list(qs.values_list('android_version', flat=True).exclude(android_version='').distinct())
        brands = list(qs.values_list('brand', flat=True).exclude(brand='').distinct())
        tps = list(qs.values_list('tp', flat=True).exclude(tp='').distinct())
        return Response({
            'hardware_versions': hardware_versions,
            'android_versions': android_versions,
            'brands': brands,
            'tps': tps,
        })


class HistorySnapshotViewSet(viewsets.ModelViewSet):
    queryset = HistorySnapshot.objects.all()
    serializer_class = HistorySnapshotSerializer

    def get_queryset(self):
        queryset = HistorySnapshot.objects.all()
        module_name = self.request.query_params.get('module_name')
        if module_name:
            queryset = queryset.filter(module_name=module_name)
        return queryset

    @action(detail=False, methods=['post'], url_path='save-snapshot')
    def save_snapshot(self, request):
        module_name = request.data.get('module_name')
        content = request.data.get('content', '')
        content_hash = request.data.get('content_hash', 0)

        if not module_name:
            return Response({'error': 'module_name is required'}, status=status.HTTP_400_BAD_REQUEST)

        last = HistorySnapshot.objects.filter(module_name=module_name).order_by('-saved_at').first()
        if last and last.content_hash == content_hash:
            return Response({'message': '内容未变化，跳过保存', 'skipped': True})

        snapshot = HistorySnapshot.objects.create(
            module_name=module_name,
            content=content,
            content_hash=content_hash,
        )
        serializer = self.get_serializer(snapshot)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='save-all-snapshots')
    def save_all_snapshots(self, request):
        modules = TaskModule.objects.all()
        saved_count = 0
        skipped_count = 0

        for mod in modules:
            today_tasks = TaskItem.objects.filter(
                module=mod, task_type='today'
            ).order_by('order', '-created_at')

            if not today_tasks.exists():
                continue

            lines = ['=== 今日任务 ===']
            for idx, item in enumerate(today_tasks, 1):
                line = f'{idx}. {item.content}'
                if item.remarks:
                    line += f'（{item.remarks}）'
                if item.is_completed:
                    line += ' [已完成]'
                lines.append(line)

            content = '\n'.join(lines)
            content_hash = hash(content)

            last = HistorySnapshot.objects.filter(module_name=mod.name).order_by('-saved_at').first()
            if last and last.content_hash == content_hash:
                skipped_count += 1
                continue

            HistorySnapshot.objects.create(
                module_name=mod.name,
                content=content,
                content_hash=content_hash,
            )
            saved_count += 1

        return Response({
            'saved': saved_count,
            'skipped': skipped_count,
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'message': '删除成功'}, status=status.HTTP_200_OK)
