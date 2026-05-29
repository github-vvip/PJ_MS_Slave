#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百度网盘分享链接 → 自动转存 → AList 获取直链 → Aria2 自动下载
=============================================================
完整工作流：
  1. 解析百度网盘分享链接 (提取 surl, pwd)
  2. 调用百度 API 转存到网盘指定目录（默认 /自动转存）
  3. 调用 AList API 刷新缓存并获取文件 302 下载直链
  4. 通过 JSON-RPC 推送给 Aria2 开始后台下载
  5. （可选）下载任务提交成功后清理百度网盘源文件

运行环境：Windows / Python 3.8+
依赖安装：pip install requests

用法：
  python main.py "https://pan.baidu.com/s/1xxxxx?pwd=yyyy"
"""

import json
import logging
import os
import re
import sys
import time
from typing import Optional, Tuple, List, Dict

import requests

# ============================================================
# 日志配置
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger('DownloadWorker')


# ============================================================
# 配置文件加载
# ============================================================
def load_config(config_path: str = None) -> dict:
    """读取 config.json 配置"""
    if config_path is None:
        # 默认查找脚本所在目录的上一级（backend/）下的 config.json
        config_path = os.path.join(
            os.path.dirname(__file__), '..', 'config.json'
        )
    config_path = os.path.abspath(config_path)

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)

    logger.info("已加载配置: %s", config_path)
    return cfg


# ============================================================
# 1. 百度网盘 API 封装
# ============================================================
class BaiduPan:
    """百度网盘客户端

    核心能力：
      - 解析分享链接
      - 初始化分享（验证提取码）
      - 转存文件到指定目录
      - 删除网盘文件（下载后清理用）
    """

    # 百度网盘 API 基础地址
    BASE_URL = 'https://pan.baidu.com'
    # app_id（固定值，与服务端约定）
    APP_ID = 250528

    def __init__(self, cookie: str, bdstoken: str,
                 save_dir: str = '/自动转存',
                 retry_times: int = 3):
        """
        Args:
            cookie: 百度网盘完整 Cookie 字符串
            bdstoken: 从百度网盘页面抓取的 bdstoken
            save_dir: 转存的目标目录，默认 /自动转存
            retry_times: API 调用失败重试次数
        """
        self.cookie = cookie.strip()
        self.bdstoken = bdstoken.strip()
        self.save_dir = save_dir if save_dir.startswith('/') else '/' + save_dir
        self.retry_times = retry_times

        # 维持会话，复用 Cookie
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/125.0.0.0 Safari/537.36'
            ),
            'Cookie': self.cookie,
            'Referer': 'https://pan.baidu.com/',
        })

    # ------------------------------------------------------------------
    # 1a. 解析分享链接
    # ------------------------------------------------------------------
    @staticmethod
    def parse_share_url(share_url: str) -> Tuple[str, str]:
        """解析百度网盘分享链接

        支持格式:
          - https://pan.baidu.com/s/1abcDefGH?pwd=1234
          - https://pan.baidu.com/s/1abcDefGH（无提取码）
          - 文字混合: 链接: ... 提取码: 1234

        Returns:
            (surl, pwd)
            例如 ('1abcDefGH', '1234')

        Raises:
            ValueError: 无法提取 surl 时
        """
        # 提取 /s/ 后面的内容
        match = re.search(r'/s/([^\s?&/]+)', share_url)
        if not match:
            raise ValueError(f"无法从链接提取 surl: {share_url}")
        surl = match.group(1).strip()

        # 尝试提取提取码（支持多种格式）
        pwd = ''
        pwd_match = re.search(r'[?&]pwd=([^&\s]+)', share_url)
        if pwd_match:
            pwd = pwd_match.group(1).strip()
        else:
            pwd_match = re.search(r'提取码\s*[:：]\s*(\w+)', share_url)
            if pwd_match:
                pwd = pwd_match.group(1).strip()

        logger.info("解析链接: surl=%s, pwd=%s", surl, '***' if pwd else '(无)')
        return surl, pwd

    # ------------------------------------------------------------------
    # 1b. 分享初始化（验证密码并获取分享 ID 和文件列表）
    # ------------------------------------------------------------------
    def _share_init(self, surl: str, pwd: str = '') -> dict:
        """初始化分享会话，验证提取码

        POST /share/init?surl={surl}

        Returns:
            dict: 含 share_id, uk, list（文件列表）等字段

        Raises:
            RuntimeError: 接口返回非零 errno
        """
        url = f'{self.BASE_URL}/share/init?surl={surl}'
        data = {'pwd': pwd or ''}

        last_err = None
        for attempt in range(1, self.retry_times + 1):
            try:
                resp = self.session.post(url, data=data, timeout=15)
                result = resp.json()
                errno = result.get('errno', -1)

                if errno == 0:
                    logger.info("分享验证通过")
                    return result['data']

                # 常见错误码处理
                if errno == 110:
                    raise RuntimeError("bdstoken 已过期 (errno=110)，请更新 config.json")
                if errno in (-130, 130):
                    raise RuntimeError("触发百度风控验证码 (errno=%d)，请更换 IP 或稍后再试" % errno)
                if errno in (3, -9):
                    raise RuntimeError(f"提取码错误 (errno={errno})")

                logger.warning("分享初始化失败 (第%d次), errno=%d, msg=%s",
                               attempt, errno, result.get('msg', ''))
                last_err = RuntimeError(f"分享初始化失败, errno={errno}")

            except requests.RequestException as e:
                logger.warning("网络请求异常 (第%d次): %s", attempt, e)
                last_err = e

            if attempt < self.retry_times:
                time.sleep(min(2 ** attempt, 8))  # 指数退避

        raise last_err or RuntimeError("分享初始化多次重试后依然失败")

    # ------------------------------------------------------------------
    # 1c. 转存文件
    # ------------------------------------------------------------------
    def transfer(self, surl: str, pwd: str = '') -> List[dict]:
        """将分享的文件转存到百度网盘 save_dir 目录

        Args:
            surl: 分享链接 surl
            pwd: 提取码

        Returns:
            转存的文件信息列表 [{server_filename, fs_id, ...}, ...]

        Raises:
            RuntimeError: 转存失败
        """
        # Step 1: 验证分享链接
        share_data = self._share_init(surl, pwd)
        share_id = share_data['share_id']
        uk = share_data['uk']
        file_list = share_data.get('list', [])

        if not file_list:
            logger.warning("分享链接中没有文件")
            return []

        filenames = [
            f.get('server_filename') or f.get('filename') or f'file_{i}'
            for i, f in enumerate(file_list)
        ]
        logger.info("待转存: %s", ', '.join(filenames))

        # Step 2: 调用转存接口
        url = f'{self.BASE_URL}/share/transfer'
        data = {
            'shareid': share_id,
            'from': uk,
            'to': self.save_dir,
            'bdstoken': self.bdstoken,
            'channel': 'chunlei',
            'web': 1,
            'app_id': self.APP_ID,
            'clienttype': 0,
        }

        last_err = None
        for attempt in range(1, self.retry_times + 1):
            try:
                resp = self.session.post(url, data=data, timeout=15)
                result = resp.json()
                errno = result.get('errno', -1)

                if errno == 0:
                    logger.info("转存成功 → %s", self.save_dir)
                    return file_list
                if errno == 110:
                    raise RuntimeError("bdstoken 已过期 (errno=110)")
                if errno == 2:
                    logger.warning("目录不存在，尝试转存到根目录 /")
                    data['to'] = '/'
                    continue  # 不计数重试
                if errno == 12:
                    raise RuntimeError("网盘空间不足 (errno=12)")
                if errno == -30:
                    raise RuntimeError("文件已存在或路径冲突 (errno=-30)")

                logger.warning("转存失败 (第%d次), errno=%d, msg=%s",
                               attempt, errno, result.get('msg', ''))
                last_err = RuntimeError(f"转存失败, errno={errno}")

            except requests.RequestException as e:
                logger.warning("网络异常 (第%d次): %s", attempt, e)
                last_err = e

            if attempt < self.retry_times:
                time.sleep(min(2 ** attempt, 8))

        raise last_err or RuntimeError("转存多次重试后依然失败")

    # ------------------------------------------------------------------
    # 1d. 删除网盘源文件（按文件名）
    # ------------------------------------------------------------------
    def delete_files(self, filenames: List[str]) -> bool:
        """删除 save_dir 下的已转存文件（任务提交成功后清理用）

        使用 filemanager 接口，opera=delete。

        Returns:
            True = 全部删除成功; False = 部分失败
        """
        if not filenames:
            return True

        filelist = [
            self.save_dir.rstrip('/') + '/' + fname
            for fname in filenames
        ]

        url = f'{self.BASE_URL}/api/filemanager'
        params = {
            'opera': 'delete',
            'bdstoken': self.bdstoken,
            'async': 2,
            'onnest': 'fail',
            'channel': 'chunlei',
            'web': 1,
            'app_id': self.APP_ID,
            'clienttype': 0,
        }

        try:
            resp = self.session.post(
                url, params=params,
                data={'filelist': json.dumps(filelist)},
                timeout=15,
            )
            result = resp.json()
            if result.get('errno') == 0:
                logger.info("源文件已清理: %s", ', '.join(filenames))
                return True
            else:
                logger.warning("清理失败: errno=%d %s",
                               result.get('errno'), result.get('msg', ''))
                return False
        except Exception as e:
            logger.error("清理异常: %s", e)
            return False


# ============================================================
# 2. AList API 封装
# ============================================================
class AListClient:
    """AList 客户端

    核心能力：
      - 刷新目录缓存
      - 获取文件的 302 下载直链（百度网盘驱动返回跳转链接）
    """

    def __init__(self, base_url: str, token: str = '',
                 retry_times: int = 5, retry_delay: int = 2):
        """
        Args:
            base_url: AList 地址 (如 http://192.168.2.108:5244)
            token: AList 管理 Token（后台 → 设置 → 其他 → Token）
            retry_times: 获取直链最大重试次数
            retry_delay: 每次重试间隔（秒）
        """
        self.base_url = base_url.rstrip('/')
        self.retry_times = retry_times
        self.retry_delay = retry_delay

        self.session = requests.Session()
        self.session.headers['User-Agent'] = (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        if token:
            self.session.headers['Authorization'] = token

    # ------------------------------------------------------------------
    # 2a. 刷新目录缓存
    # ------------------------------------------------------------------
    def refresh_path(self, path: str) -> bool:
        """强制刷新 AList 指定路径的缓存（使用 refresh=true 参数）

        Returns:
            True = 刷新成功
        """
        try:
            resp = self.session.post(
                f'{self.base_url}/api/fs/list',
                json={
                    'path': path,
                    'password': '',
                    'page': 1,
                    'per_page': 0,
                    'refresh': True,      # 关键：强制刷新缓存
                },
                timeout=30,
            )
            result = resp.json()
            ok = result.get('code') == 200
            logger.info("AList 刷新 %s: %s", path, '成功' if ok else '失败')
            return ok
        except Exception as e:
            logger.warning("AList 刷新异常: %s", e)
            return False

    # ------------------------------------------------------------------
    # 2b. 获取单个文件直链
    # ------------------------------------------------------------------
    def get_direct_link(self, file_path: str) -> Optional[str]:
        """获取文件的 302 下载直链（raw_url）

        针对百度网盘存储类型，AList 返回一个 302 跳转 URL，
        Aria2 可直接使用此链接下载（自动跟随跳转）。

        Args:
            file_path: 在 AList 中的完整路径

        Returns:
            str: 直链 URL，失败返回 None
        """
        for attempt in range(1, self.retry_times + 1):
            try:
                resp = self.session.post(
                    f'{self.base_url}/api/fs/get',
                    json={'path': file_path, 'password': ''},
                    timeout=15,
                )
                result = resp.json()

                if result.get('code') != 200:
                    logger.warning("获取文件信息失败 (第%d次): %s",
                                   attempt, result.get('message', ''))
                    time.sleep(self.retry_delay)
                    continue

                raw_url = result.get('data', {}).get('raw_url')
                if raw_url:
                    logger.info("获取直链成功: %s", file_path)
                    return raw_url

                # raw_url 为空 → 文件尚未被 AList 缓存或转存尚未同步
                logger.info("直链未就绪 (第%d次), 等待 %ds...",
                            attempt, self.retry_delay)

                # 每2次重试触发一次刷新
                if attempt % 2 == 0:
                    parent_dir = os.path.dirname(file_path)
                    self.refresh_path(parent_dir)

                time.sleep(self.retry_delay)

            except requests.RequestException as e:
                logger.warning("请求异常 (第%d次): %s", attempt, e)
                time.sleep(self.retry_delay)

        logger.error("直链获取失败 (已达最大重试 %d 次): %s", self.retry_times, file_path)
        return None

    # ------------------------------------------------------------------
    # 2c. 批量获取直链
    # ------------------------------------------------------------------
    def get_direct_links(self, alist_dir: str,
                         filenames: List[str]) -> Dict[str, str]:
        """批量获取多个文件的直链

        Returns:
            {filename: direct_url, ...} 仅包含成功获取的项
        """
        base_dir = alist_dir.rstrip('/')
        result = {}
        for fname in filenames:
            url = self.get_direct_link(f'{base_dir}/{fname}')
            if url:
                result[fname] = url
            else:
                logger.warning("跳过直链获取失败的文件: %s", fname)
        return result


# ============================================================
# 3. Aria2 JSON-RPC 封装
# ============================================================
class Aria2RPC:
    """Aria2 下载客户端

    使用 JSON-RPC over HTTP 协议与 Aria2 进程通信。
    """

    def __init__(self, rpc_url: str, secret: str = '',
                 download_dir: str = '', retry_times: int = 3):
        """
        Args:
            rpc_url: RPC 地址 (如 http://192.168.2.108:6800/jsonrpc)
            secret: --rpc-secret 配置的密钥（没有则留空）
            download_dir: 本地文件保存路径
            retry_times: 失败重试次数
        """
        self.rpc_url = rpc_url
        self.secret = secret.strip()
        self.download_dir = download_dir.replace('\\', '/') if download_dir else ''
        self.retry_times = retry_times

        self.session = requests.Session()
        self.session.headers['Content-Type'] = 'application/json'

    # ------------------------------------------------------------------
    # 3a. 通用 RPC 调用
    # ------------------------------------------------------------------
    def _call(self, method: str, params: list) -> Optional[dict]:
        """执行 Aria2 JSON-RPC 方法

        自动在参数列表开头插入 token:xxx（如有配置密钥）。
        """
        rpc_params = (
            [f'token:{self.secret}'] + params
            if self.secret else params
        )
        payload = {
            'jsonrpc': '2.0',
            'id': int(time.time() * 1000),
            'method': method,
            'params': rpc_params,
        }

        for attempt in range(1, self.retry_times + 1):
            try:
                resp = self.session.post(
                    self.rpc_url, json=payload, timeout=30,
                )
                result = resp.json()

                if 'error' in result:
                    err = result['error']
                    code = err.get('code', -1)
                    msg = err.get('message', '')
                    logger.warning("RPC 错误 (第%d次): [%d] %s", attempt, code, msg)
                    if code == 1:
                        raise RuntimeError(f"Aria2 下载失败: {msg}")
                    if attempt < self.retry_times:
                        time.sleep(2)
                    continue

                return result.get('result')

            except (requests.RequestException, ValueError) as e:
                logger.warning("RPC 连接异常 (第%d次): %s", attempt, e)
                if attempt < self.retry_times:
                    time.sleep(2)

        return None

    # ------------------------------------------------------------------
    # 3b. 添加下载任务
    # ------------------------------------------------------------------
    def add_download(self, url: str, filename: str = '',
                     extra_headers: List[str] = None) -> Optional[str]:
        """添加 HTTP 下载任务

        Args:
            url: 下载直链
            filename: 自定义保存文件名（留空由 Aria2 自动检测）
            extra_headers: 额外 HTTP 请求头 ["Key: Value", ...]

        Returns:
            str: Aria2 任务 GID（全局唯一标识），失败返回 None
        """
        options = {}
        if self.download_dir:
            options['dir'] = self.download_dir
        if filename:
            options['out'] = filename
        if extra_headers:
            options['header'] = extra_headers

        # 百度网盘直链建议启用并发分片下载，加速完成
        options['max-connection-per-server'] = '4'
        options['split'] = '4'

        logger.info("提交下载: %s → %s/%s", url, options.get('dir', '默认'), filename)

        gid = self._call('aria2.addUri', [[url], options])
        if gid:
            logger.info("→ 任务已提交, GID: %s", gid)
        else:
            logger.error("→ 任务提交失败: %s", filename)
        return gid


# ============================================================
# 4. 工作流编排
# ============================================================
class DownloadWorkflow:
    """百度网盘 → AList → Aria2 全链路编排器"""

    def __init__(self, config_path: str = None):
        cfg = load_config(config_path)

        # 初始化各客户端
        baidu_cfg = cfg['baidu']
        self.baidu = BaiduPan(
            cookie=baidu_cfg['cookie'],
            bdstoken=baidu_cfg['bdstoken'],
            save_dir=baidu_cfg.get('save_dir', '/自动转存'),
            retry_times=baidu_cfg.get('retry_times', 3),
        )

        alist_cfg = cfg['alist']
        self.alist = AListClient(
            base_url=alist_cfg['base_url'],
            token=alist_cfg.get('token', ''),
            retry_times=alist_cfg.get('retry_times', 5),
            retry_delay=alist_cfg.get('retry_delay', 2),
        )

        aria2_cfg = cfg.get('aria2', {})
        self.aria2 = Aria2RPC(
            rpc_url=aria2_cfg.get('rpc_url', 'http://127.0.0.1:6800/jsonrpc'),
            secret=aria2_cfg.get('secret', ''),
            download_dir=aria2_cfg.get('download_dir', ''),
            retry_times=aria2_cfg.get('retry_times', 3),
        )

        # AList 上百度网盘存储的挂载路径（含存储桶前缀）
        self.alist_path = alist_cfg.get('baidu_storage_path', '')

        # 是否在下载任务提交后清理百度网盘源文件
        self.cleanup_enabled = cfg.get('cleanup', {}).get('delete_source', False)

    def run(self, share_url: str) -> bool:
        """执行完整工作流

        Returns:
            True = 所有步骤成功; False = 任何步骤失败
        """
        log = logger
        log.info("=" * 60)
        log.info("启动下载工作流")
        log.info("=" * 60)

        # ----- Step 1: 解析链接 -----
        try:
            surl, pwd = self.baidu.parse_share_url(share_url)
        except ValueError as e:
            log.error("链接解析失败: %s", e)
            return False

        # ----- Step 2: 转存到百度网盘 -----
        try:
            file_list = self.baidu.transfer(surl, pwd)
            if not file_list:
                log.warning("无文件可转存")
                return False
        except RuntimeError as e:
            log.error("转存失败: %s", e)
            return False

        filenames = [f.get('server_filename') or f.get('filename', '')
                     for f in file_list]
        filenames = [f for f in filenames if f]
        log.info("待下载文件: %s", ', '.join(filenames))

        # ----- Step 3: AList 获取直链 -----
        if not self.alist_path:
            log.error("config.json 未配置 alist.baidu_storage_path")
            return False

        # 短等片刻，让 AList 感知到文件变化
        log.info("等待 AList 同步(3s)...")
        time.sleep(3)
        self.alist.refresh_path(self.alist_path)

        links = self.alist.get_direct_links(self.alist_path, filenames)
        if not links:
            log.error("未获取到任何直链，流程终止")
            return False
        log.info("获取直链 %d/%d", len(links), len(filenames))

        # ----- Step 4: 推送 Aria2 下载 -----
        success_files, failed_files = [], []
        for fname, url in links.items():
            gid = self.aria2.add_download(url, filename=fname)
            if gid:
                success_files.append(fname)
            else:
                failed_files.append(fname)

        if success_files:
            log.info("下载已提交: %s", ', '.join(success_files))
        if failed_files:
            log.warning("下载提交失败: %s", ', '.join(failed_files))

        # ----- Step 5: 可选清理 -----
        if self.cleanup_enabled and success_files:
            log.info("清理百度网盘源文件...")
            self.baidu.delete_files(success_files)

        return len(failed_files) == 0


# ============================================================
# 命令行入口
# ============================================================
def main():
    if len(sys.argv) < 2:
        print("用法: python main.py <百度网盘分享链接> [配置文件路径]")
        print("示例: python main.py 'https://pan.baidu.com/s/1abcDefGH?pwd=1234'")
        sys.exit(1)

    share_url = sys.argv[1].strip()
    config_path = sys.argv[2] if len(sys.argv) >= 3 else None

    try:
        workflow = DownloadWorkflow(config_path)
        ok = workflow.run(share_url)
    except Exception as e:
        logger.exception("工作流出错")
        ok = False

    if ok:
        logger.info("工作流执行完成 ✓")
        sys.exit(0)
    else:
        logger.error("工作流执行失败 ✗")
        sys.exit(1)


if __name__ == '__main__':
    main()
