"""
Django 项目 URL 配置
"""
from django.contrib import admin
from django.urls import path, include
from django.views.static import serve
from django.conf import settings
from django.http import HttpResponse
import os


def serve_vue_app(request, path=''):
    """托管 Vue 打包后的静态文件，所有非 API 路由均返回 index.html"""
    vue_dist = settings.VUE_DIST_DIR
    file_path = vue_dist / path
    if path and os.path.isfile(file_path):
        return serve(request, path, document_root=vue_dist)
    index_file = vue_dist / 'index.html'
    if os.path.isfile(index_file):
        with open(index_file, 'rb') as f:
            return HttpResponse(f.read(), content_type='text/html')
    return HttpResponse('请先执行 npm run build 打包前端文件', status=404)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('assets/<path:path>', serve, {'document_root': settings.VUE_DIST_DIR / 'assets'}),
    path('DBbackup/<path:path>', serve, {'document_root': 'E:/PJ_MS_Slave/DBbackup'}),
    path('', serve_vue_app, name='vue-app'),
    path('<path:path>', serve_vue_app, name='vue-app-catch-all'),
]
