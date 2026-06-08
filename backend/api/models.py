"""
数据模型定义
包含四个模型：TaskModule、TaskItem、Customer、Project
"""
from django.db import models


class TaskModule(models.Model):
    """任务模块：如"项目A"、"日常事务"等，每个模块默认包含今日任务和待办任务池"""
    name = models.CharField('名称', max_length=100)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = '任务模块'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class TaskItem(models.Model):
    """任务项：通过 task_type 区分今日任务('today')和待办任务('todo')"""
    TASK_TYPE_CHOICES = [
        ('today', '今日任务'),
        ('todo', '待办任务'),
    ]
    module = models.ForeignKey(TaskModule, on_delete=models.CASCADE, related_name='tasks', verbose_name='所属任务模块')
    task_type = models.CharField('任务类型', max_length=10, choices=TASK_TYPE_CHOICES, default='todo')
    order = models.PositiveIntegerField('排序序号', default=0)
    content = models.TextField('任务内容')
    remarks = models.TextField('备注', blank=True, default='')
    is_completed = models.BooleanField('是否完成', default=False)
    postpone_tomorrow = models.BooleanField('推迟到明天', default=False)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = '任务项'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.get_task_type_display()} - {self.content[:30]}'


class HistorySnapshot(models.Model):
    module_name = models.CharField('模块名称', max_length=100)
    content = models.TextField('快照内容')
    saved_at = models.DateTimeField('保存时间', auto_now_add=True)
    content_hash = models.IntegerField('内容哈希', default=0)

    class Meta:
        ordering = ['-saved_at']
        verbose_name = '历史快照'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.module_name} - {self.saved_at.strftime("%Y-%m-%d %H:%M")}'


class Customer(models.Model):
    """客户表：按客户分组管理项目"""
    name = models.CharField('客户名称', max_length=100, unique=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = '客户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Project(models.Model):
    """项目配置表：硬件项目信息管理，按客户分组"""
    LIGHT_SENSOR_CHOICES = [
        ('ADCF3', 'ADCF3'),
        ('STK3311', 'STK3311'),
        ('无', '无'),
    ]
    WIFI_CHOICES = [
        ('2.4G', '2.4G'),
        ('5G', '5G'),
    ]
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='projects', verbose_name='所属客户')
    serial_number = models.PositiveIntegerField('序号')
    hardware_version = models.CharField('硬件版型', max_length=100, blank=True, default='')
    project_name = models.CharField('项目名称', max_length=100)
    android_version = models.CharField('Android版本', max_length=50, blank=True, default='')
    brand = models.CharField('厂商', max_length=50, blank=True, default='')
    model = models.CharField('型号', max_length=50, blank=True, default='')
    launcher = models.CharField('Launcher', max_length=50, blank=True, default='')
    pir = models.BooleanField('PIR', default=False)
    led = models.BooleanField('LED', default=False)
    light_sensor = models.CharField('光感', max_length=20, choices=LIGHT_SENSOR_CHOICES, default='无')
    wifi = models.CharField('WiFi', max_length=10, choices=WIFI_CHOICES, default='2.4G')
    screen_size = models.CharField('屏幕尺寸', max_length=20, blank=True, default='')
    screen_model = models.CharField('屏幕型号', max_length=100, blank=True, default='')
    tp = models.CharField('TP', max_length=100, blank=True, default='')
    shell = models.CharField('壳', max_length=100, blank=True, default='')
    project_establish_date = models.DateField('立项时间', null=True, blank=True)
    remarks = models.TextField('备注', blank=True, default='')

    class Meta:
        ordering = ['serial_number']
        unique_together = [['customer', 'serial_number']]
        verbose_name = '项目配置'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.serial_number}. {self.project_name}'
