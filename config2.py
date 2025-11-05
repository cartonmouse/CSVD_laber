"""
配置文件：管理标签、路径和导出格式
"""

import os
from pathlib import Path

# ==================== 路径配置 ====================
# 视频文件夹路径（请根据实际情况修改）
VIDEO_DIR = r"G:\huafeng_seg\崔丙强_PU_20005558"

# 标注数据保存路径
ANNOTATION_DIR = r"G:\huafeng_labeled\崔丙强_PU_20005558"

# 导出的JSON文件路径
EXPORT_JSON = r"G:\huafeng_labeled\崔丙强_PU_20005558"


# ==================== 预定义标签 ====================
DEFAULT_TAGS = [
    "安全帽佩戴",
    "安全绳使用",
    "高空作业",
    "脚手架作业",
    "焊接",
    "切割",
    "吊装",
    "搬运材料",
    "浇筑混凝土",
    "钢筋绑扎",
    "模板安装",
    "抹灰",
    "砌墙",
    "电气安装",
    "管道安装",
    "测量放线",
    "安全检查",
    "危险行为",
    "机械操作",
    "清理现场",
]


# ==================== 界面配置 ====================
# 窗口大小
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900

# 视频播放器大小
VIDEO_WIDTH = 800
VIDEO_HEIGHT = 600


# ==================== 数据格式定义 ====================
def get_annotation_template():
    """
    返回单个视频的标注数据模板
    """
    return {
        "video_path": "",
        "video_name": "",
        "duration": 0.0,
        "segments": [],
        "annotated": False,
        "annotator": "",
        "timestamp": ""
    }


def get_segment_template():
    """
    返回单个片段的标注模板
    """
    return {
        "start_time": 0.0,
        "end_time": 0.0,
        "description": "",
        "noun": "",      # 新增
        "verb": "",      # 新增
        "tags": []
    }


# ==================== 初始化函数 ====================
def init_directories():
    """
    创建必要的目录
    """
    Path(ANNOTATION_DIR).mkdir(parents=True, exist_ok=True)
    Path(EXPORT_JSON).parent.mkdir(parents=True, exist_ok=True)