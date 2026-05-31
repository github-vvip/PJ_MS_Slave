"""
DRF 视图集
"""
import os
import re
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
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


# ============================================================
# 配置雷达 — 网络路径检索
# ============================================================

# Android版本映射（二级文件夹名 → 版本号）
ANDROID_VERSION_MAP = {
    'rk_m': '6',
    'rk_r': '11',
    'rk_s': '12',
    'rk_t': '13',
    'rk_u': '14',
    'rk_v': '15',
}

# Launcher 推导规则（项目名称关键词 → Launcher 值）
LAUNCHER_RULES = [
    ('photo', 'WP'),
    ('frame', 'FM'),
    ('whaleframely', 'WF'),
    ('fcalendar', 'FC'),
]

DEFAULT_LAUNCHER = 'OM'

# 客户名称中需要剔除的关键词
EXCLUDED_KEYWORDS = ['智象', '日历']


@api_view(['POST'])
def search_projects(request):
    """
    检索网络路径中的项目配置信息
    POST /api/search/
    遍历 \\\\192.168.2.18\\work\\需求 文件夹层级，解析配置字段
    """
    root_path = r'\\192.168.2.18\work\需求'

    # 检查根路径是否可访问
    if not os.path.isdir(root_path):
        return Response({
            'code': 500,
            'message': f'网络路径不可访问: {root_path}',
            'data': []
        })

    results = []

    # ---- 遍历二级文件夹：解析 Android 版本 ----
    try:
        level2_dirs = [d for d in os.listdir(root_path)
                       if os.path.isdir(os.path.join(root_path, d))]
    except PermissionError:
        return Response({'code': 500, 'message': '无权限访问网络路径', 'data': []})

    for l2_dir in sorted(level2_dirs):
        android_version = _get_android_version(l2_dir)
        l2_path = os.path.join(root_path, l2_dir)

        # ---- 遍历三级文件夹：解析硬件版型 ----
        try:
            level3_dirs = [d for d in os.listdir(l2_path)
                           if os.path.isdir(os.path.join(l2_path, d))]
        except PermissionError:
            continue

        for l3_dir in sorted(level3_dirs):
            hardware_version = l3_dir  # 文件夹名即为硬件版型
            l3_path = os.path.join(l2_path, l3_dir)

            # ---- 遍历四级文件夹：解析客户/厂商/项目名称 ----
            try:
                level4_dirs = [d for d in os.listdir(l3_path)
                               if os.path.isdir(os.path.join(l3_path, d))]
            except PermissionError:
                continue

            for l4_dir in sorted(level4_dirs):
                customer, vendor, project_name_l4 = _parse_level4(l4_dir)
                l4_path = os.path.join(l3_path, l4_dir)
                project_name = project_name_l4

                # 读取五级文件夹
                level5_dirs = []
                try:
                    level5_dirs = [d for d in os.listdir(l4_path)
                                   if os.path.isdir(os.path.join(l4_path, d))]
                except PermissionError:
                    pass

                excel_path = None

                # 如果四级文件夹不是纯汉字名称，配置表可能在四级文件夹内
                if not re.fullmatch(r'[一-鿿]+', l4_dir):
                    excel_path = _find_excel_file(l4_path)

                if not excel_path:
                    if not project_name:
                        # 四级只有客户名，到五级文件夹找项目名称
                        project_name, excel_path = _search_project_in_level5(
                            level5_dirs, l4_path
                        )
                        # 五级未找到 Excel，尝试六级
                        if not excel_path:
                            excel_path = _search_excel_in_level6(
                                level5_dirs, l4_path
                            )
                    else:
                        # 四级已有客户+项目名，到五级找 Excel
                        excel_path = _search_excel_in_level5(level5_dirs, l4_path)
                        # 五级未找到，尝试六级
                        if not excel_path:
                            excel_path = _search_excel_in_level6(
                                level5_dirs, l4_path
                            )

                # 推导 Launcher
                launcher = _derive_launcher(project_name or '')

                # 只有同时有客户和项目名称才加入结果，"新需求"不作为客户
                if customer and project_name and customer != '新需求':
                    results.append({
                        '客户': customer,
                        '厂商': vendor,
                        '项目名称': project_name,
                        '硬件版型': hardware_version,
                        'Android版本': android_version,
                        'Launcher': launcher,
                        '配置表路径': excel_path or '',
                    })

    return Response({
        'code': 200,
        'message': 'success',
        'data': results,
    })


def _get_android_version(folder_name):
    """根据二级文件夹名映射 Android 版本"""
    name_lower = folder_name.lower()
    if 'linux' in name_lower or 'debian' in name_lower:
        return 'Debian11'
    for key, version in ANDROID_VERSION_MAP.items():
        if key in name_lower:
            return version
    return folder_name  # 无法匹配则返回原名称


def _parse_level4(folder_name):
    """
    解析四级文件夹名
    返回: (customer, vendor, project_name)
    - 纯汉字 → 客户=汉字，无项目名称
    - 汉字混合其它 → 有"-"时取第一个"-"左边的汉字作为客户(剔除"智象""日历")
    - 客户 == 厂商
    """
    # 情况1：纯汉字（无项目名称）
    if re.fullmatch(r'[一-鿿]+', folder_name):
        return folder_name.strip('-'), folder_name.strip('-'), None

    # 情况2：汉字混合其它字符
    if '-' in folder_name:
        # 有"-"时，只取第一个"-"左边的部分提取汉字作为客户
        left_part = folder_name.split('-')[0]
        chinese_chars = re.findall(r'[一-鿿]+', left_part)
    else:
        # 无"-"时，从整个文件夹名提取汉字
        chinese_chars = re.findall(r'[一-鿿]+', folder_name)
    customer = ''.join(chinese_chars)

    # 剔除"智象"、"日历"关键词
    for kw in EXCLUDED_KEYWORDS:
        customer = customer.replace(kw, '')

    if not customer:
        # 无汉字，整个文件夹名即为厂商和客户
        return folder_name.strip('-'), folder_name.strip('-'), None

    # 项目名称 = 剔除汉字部分，并去掉两侧的 "-"
    project_name = re.sub(r'[一-鿿]+', '', folder_name).strip('-')

    vendor = customer
    customer = customer.strip('-')

    return customer, vendor, project_name if project_name else None


def _parse_level5_project_name(folder_name):
    """
    解析五级文件夹名为项目名称
    - 无汉字 → 整个文件夹名即为项目名称
    - 汉字混合其它 → 剔除汉字后为项目名称
    """
    has_chinese = bool(re.search(r'[一-鿿]', folder_name))
    if not has_chinese:
        return folder_name.strip('-')
    # 剔除汉字，保留剩余部分
    project_name = re.sub(r'[一-鿿]+', '', folder_name).strip('-')
    return project_name if project_name else None


def _find_excel_file(directory):
    """
    在目录中查找订单软硬件配置表 Excel 文件
    匹配规则：文件名包含"订单"/"软硬"/"硬件"/"配置"/"表" 任一关键词 + .xlsx/.xls
    多个匹配时取文件名最长的
    """
    if not os.path.isdir(directory):
        return None
    matched_files = []
    try:
        for f in os.listdir(directory):
            if not (f.endswith('.xlsx') or f.endswith('.xls')):
                continue
            name = os.path.splitext(f)[0]
            keywords = ['订单', '软硬', '硬件', '配置', '表']
            if any(kw in name for kw in keywords):
                matched_files.append(f)
    except PermissionError:
        pass
    if not matched_files:
        return None
    # 选文件名最长的
    best = max(matched_files, key=lambda f: len(os.path.splitext(f)[0]))
    return os.path.join(directory, best)


def _derive_launcher(project_name):
    """根据项目名称推导 Launcher 类型（不区分大小写匹配）"""
    name_lower = project_name.lower()
    for keyword, launcher in LAUNCHER_RULES:
        if keyword in name_lower:
            return launcher
    return DEFAULT_LAUNCHER


def _search_project_in_level5(level5_dirs, l4_path):
    """在五级文件夹中查找项目名称和 Excel 文件"""
    for l5_dir in sorted(level5_dirs):
        l5_project = _parse_level5_project_name(l5_dir)
        if l5_project:
            l5_path = os.path.join(l4_path, l5_dir)
            excel_path = _find_excel_file(l5_path)
            if excel_path:
                return l5_project, excel_path
    return None, None


def _search_excel_in_level5(level5_dirs, l4_path):
    """在五级文件夹中查找 Excel 文件"""
    for l5_dir in sorted(level5_dirs):
        l5_path = os.path.join(l4_path, l5_dir)
        excel_path = _find_excel_file(l5_path)
        if excel_path:
            return excel_path
    return None


def _search_excel_in_level6(level5_dirs, l4_path):
    """在六级文件夹中查找 Excel 文件"""
    for l5_dir in sorted(level5_dirs):
        l5_path = os.path.join(l4_path, l5_dir)
        try:
            level6_dirs = [d for d in os.listdir(l5_path)
                           if os.path.isdir(os.path.join(l5_path, d))]
        except PermissionError:
            continue
        for l6_dir in sorted(level6_dirs):
            l6_path = os.path.join(l5_path, l6_dir)
            excel_path = _find_excel_file(l6_path)
            if excel_path:
                return excel_path
    return None
