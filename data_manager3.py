"""
数据管理模块：负责视频列表、标注数据的读写和管理
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import cv2

from config import (
    VIDEO_DIR,
    ANNOTATION_DIR,
    EXPORT_JSON,
    DEFAULT_TAGS,
    get_annotation_template,
    get_segment_template
)


class DataManager:
    """数据管理类"""

    def __init__(self):
        self.video_list = []
        self.current_tags = DEFAULT_TAGS.copy()
        self.load_video_list()

    def load_video_list(self) -> List[str]:
        """
        从VIDEO_DIR递归加载所有mp4视频文件
        """
        video_dir = Path(VIDEO_DIR)
        if not video_dir.exists():
            self.video_list = []
            return []

        # 递归查找所有mp4文件
        self.video_list = sorted([
            str(f) for f in video_dir.rglob("*.mp4")
        ])
        return self.video_list

    def get_video_count(self) -> int:
        """获取视频总数"""
        return len(self.video_list)

    def get_video_path(self, index: int) -> Optional[str]:
        """根据索引获取视频路径"""
        if 0 <= index < len(self.video_list):
            return self.video_list[index]
        return None

    def get_video_display_name(self, video_path: str) -> str:
        """
        生成友好的显示名称
        例如: PU_20005657_0_20250816_113900/seg_000
        """
        path = Path(video_path)
        parent_name = path.parent.name
        file_name = path.stem

        if parent_name and parent_name != Path(VIDEO_DIR).name:
            return f"{parent_name}/{file_name}"
        return file_name

    def get_video_duration(self, video_path: str) -> float:
        """获取视频时长（秒）"""
        try:
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            cap.release()

            if fps > 0:
                return frame_count / fps
            return 0.0
        except Exception as e:
            print(f"Error getting video duration: {e}")
            return 0.0

    def get_annotation_path(self, video_path: str) -> str:
        """根据视频路径生成对应的标注文件路径"""
        # 保持目录结构
        relative_path = Path(video_path).relative_to(VIDEO_DIR)
        annotation_path = Path(ANNOTATION_DIR) / relative_path.parent / f"{relative_path.stem}.json"

        # 确保目录存在
        annotation_path.parent.mkdir(parents=True, exist_ok=True)

        return str(annotation_path)

    def load_annotation(self, video_path: str) -> Dict:
        """
        加载某个视频的标注数据
        如果不存在则返回空模板
        """
        annotation_path = self.get_annotation_path(video_path)

        if os.path.exists(annotation_path):
            try:
                with open(annotation_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading annotation: {e}")

        # 返回新模板
        template = get_annotation_template()
        template['video_path'] = video_path
        template['video_name'] = Path(video_path).name
        template['duration'] = self.get_video_duration(video_path)
        return template

    def save_annotation(self, video_path: str, annotation_data: Dict) -> bool:
        """
        保存标注数据到JSON文件
        """
        annotation_path = self.get_annotation_path(video_path)

        try:
            # 更新时间戳
            annotation_data['timestamp'] = datetime.now().isoformat()

            with open(annotation_path, 'w', encoding='utf-8') as f:
                json.dump(annotation_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving annotation: {e}")
            return False

    def get_annotated_count(self) -> int:
        """统计已标注的视频数量"""
        count = 0
        for video_path in self.video_list:
            annotation = self.load_annotation(video_path)
            if annotation.get('annotated', False):
                count += 1
        return count

    def export_all_annotations(self) -> bool:
        """
        导出所有标注数据到单个JSON文件
        """
        all_annotations = []

        for video_path in self.video_list:
            annotation = self.load_annotation(video_path)
            if annotation.get('segments'):  # 只导出有片段的标注
                all_annotations.append(annotation)

        try:
            with open(EXPORT_JSON, 'w', encoding='utf-8') as f:
                json.dump({
                    'total_videos': len(all_annotations),
                    'export_time': datetime.now().isoformat(),
                    'annotations': all_annotations
                }, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error exporting annotations: {e}")
            return False

    def add_tag(self, new_tag: str) -> bool:
        """添加新标签"""
        if new_tag and new_tag not in self.current_tags:
            self.current_tags.append(new_tag)
            return True
        return False

    def get_video_status(self, video_path: str) -> str:
        """
        获取视频状态
        返回: "未标注" / "已标注" / "非必要"
        """
        annotation = self.load_annotation(video_path)
        status = annotation.get('status', '未标注')

        # 自动更新状态：如果有片段则标记为已标注
        if annotation.get('segments') and status == '未标注':
            status = '已标注'
            annotation['status'] = status
            self.save_annotation(video_path, annotation)

        return status

    def set_video_status(self, video_path: str, status: str) -> bool:
        """
        设置视频状态
        status: "未标注" / "已标注" / "非必要"
        """
        if status not in ["未标注", "已标注", "非必要"]:
            return False

        annotation = self.load_annotation(video_path)
        annotation['status'] = status
        return self.save_annotation(video_path, annotation)

    def get_status_counts(self) -> dict:
        """
        统计各状态的视频数量
        返回: {"未标注": int, "已标注": int, "非必要": int}
        """
        counts = {"未标注": 0, "已标注": 0, "非必要": 0}

        for video_path in self.video_list:
            status = self.get_video_status(video_path)
            counts[status] = counts.get(status, 0) + 1

        return counts

    def get_tags(self) -> List[str]:
        """获取当前所有标签"""
        return self.current_tags.copy()

    def create_segment(self, start_time: float, end_time: float,
                      description: str = "", tags: List[str] = None) -> Dict:
        """创建一个新的片段"""
        segment = get_segment_template()
        segment['start_time'] = start_time
        segment['end_time'] = end_time
        segment['description'] = description
        segment['tags'] = tags or []
        return segment