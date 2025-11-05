"""
视频标注界面模块：核心标注功能
"""

import streamlit as st
from typing import List, Dict, Optional
from datetime import timedelta


class VideoAnnotator:
    """视频标注界面类"""

    def __init__(self, data_manager):
        self.data_manager = data_manager

    def format_time(self, seconds: float) -> str:
        """将秒数格式化为 MM:SS.mmm"""
        td = timedelta(seconds=seconds)
        total_seconds = int(td.total_seconds())
        milliseconds = int((seconds - total_seconds) * 1000)
        minutes = total_seconds // 60
        secs = total_seconds % 60
        return f"{minutes:02d}:{secs:02d}.{milliseconds:03d}"

    def parse_time(self, time_str: str) -> Optional[float]:
        """将时间字符串解析为秒数"""
        try:
            parts = time_str.split(':')
            if len(parts) == 2:
                minutes, seconds = parts
                seconds_parts = seconds.split('.')
                secs = int(seconds_parts[0])
                ms = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
                return int(minutes) * 60 + secs + ms / 1000
            return None
        except:
            return None

    def render_video_player(self, video_path: str):
        """渲染视频播放器"""
        st.subheader("📹 视频预览")

        # 显示视频
        video_file = open(video_path, 'rb')
        video_bytes = video_file.read()
        st.video(video_bytes)
        video_file.close()

    def render_segment_input(self, video_duration: float) -> Optional[Dict]:
        """渲染片段输入区域"""
        st.subheader("➕ 添加新片段")

        col1, col2 = st.columns(2)

        with col1:
            start_input = st.text_input(
                "开始时间 (MM:SS.mmm)",
                value="00:00.000",
                key="start_time_input",
                help="格式: 分:秒.毫秒，例如 00:05.500"
            )

        with col2:
            end_input = st.text_input(
                "结束时间 (MM:SS.mmm)",
                value="00:00.000",
                key="end_time_input",
                help="格式: 分:秒.毫秒，例如 00:10.500"
            )

        # 解析时间
        start_time = self.parse_time(start_input)
        end_time = self.parse_time(end_input)

        # 验证时间
        time_valid = True
        if start_time is None or end_time is None:
            st.warning("⚠️ 时间格式错误，请使用 MM:SS.mmm 格式")
            time_valid = False
        elif start_time >= end_time:
            st.warning("⚠️ 开始时间必须小于结束时间")
            time_valid = False
        elif end_time > video_duration:
            st.warning(f"⚠️ 结束时间超出视频时长 ({self.format_time(video_duration)})")
            time_valid = False

        # 文本描述
        description = st.text_area(
            "片段描述",
            placeholder="描述这个片段中发生的事情...",
            key="description_input",
            height=100
        )

        # 标签选择
        tags = self.render_tag_selector()

        # 添加按钮
        if st.button("✅ 添加片段", type="primary", disabled=not time_valid):
            if time_valid:
                return self.data_manager.create_segment(
                    start_time=start_time,
                    end_time=end_time,
                    description=description,
                    tags=tags
                )

        return None

    def render_tag_selector(self) -> List[str]:
        """渲染标签选择器"""
        st.markdown("**标签选择**")

        available_tags = self.data_manager.get_tags()

        # 多选标签
        selected_tags = st.multiselect(
            "选择标签（可多选）",
            options=available_tags,
            key="tag_selector"
        )

        # 添加新标签
        with st.expander("➕ 添加自定义标签"):
            new_tag = st.text_input("新标签名称", key="new_tag_input")
            if st.button("添加标签", key="add_tag_button"):
                if new_tag:
                    if self.data_manager.add_tag(new_tag):
                        st.success(f"✅ 已添加标签: {new_tag}")
                        st.rerun()
                    else:
                        st.warning("标签已存在")

        return selected_tags

    def render_segment_list(self, segments: List[Dict],
                            annotation_data: Dict) -> List[Dict]:
        """
        渲染已标注的片段列表
        返回更新后的片段列表
        """
        st.subheader(f"📋 已标注片段 ({len(segments)})")

        if not segments:
            st.info("暂无标注片段，请添加新片段")
            return segments

        updated_segments = segments.copy()

        for idx, segment in enumerate(segments):
            with st.expander(
                    f"片段 {idx + 1}: {self.format_time(segment['start_time'])} - "
                    f"{self.format_time(segment['end_time'])}"
            ):
                # 显示片段信息
                st.markdown(f"**时间范围:** {self.format_time(segment['start_time'])} → "
                            f"{self.format_time(segment['end_time'])} "
                            f"(时长: {self.format_time(segment['end_time'] - segment['start_time'])})")

                st.markdown(f"**描述:** {segment['description'] or '(无描述)'}")

                if segment['tags']:
                    tags_display = ", ".join([f"`{tag}`" for tag in segment['tags']])
                    st.markdown(f"**标签:** {tags_display}")
                else:
                    st.markdown("**标签:** (无标签)")

                # 操作按钮
                col1, col2 = st.columns([1, 1])

                with col1:
                    if st.button("✏️ 编辑", key=f"edit_{idx}"):
                        st.session_state[f'editing_{idx}'] = True
                        st.rerun()

                with col2:
                    if st.button("🗑️ 删除", key=f"delete_{idx}"):
                        updated_segments.pop(idx)
                        st.success("已删除片段")
                        return updated_segments

                # 编辑模式
                if st.session_state.get(f'editing_{idx}', False):
                    st.markdown("---")
                    st.markdown("**编辑片段**")

                    # 编辑描述
                    new_description = st.text_area(
                        "描述",
                        value=segment['description'],
                        key=f"edit_desc_{idx}",
                        height=100
                    )

                    # 编辑标签
                    new_tags = st.multiselect(
                        "标签",
                        options=self.data_manager.get_tags(),
                        default=segment['tags'],
                        key=f"edit_tags_{idx}"
                    )

                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if st.button("💾 保存", key=f"save_{idx}"):
                            updated_segments[idx]['description'] = new_description
                            updated_segments[idx]['tags'] = new_tags
                            st.session_state[f'editing_{idx}'] = False
                            st.success("已保存修改")
                            return updated_segments

                    with col2:
                        if st.button("❌ 取消", key=f"cancel_{idx}"):
                            st.session_state[f'editing_{idx}'] = False
                            st.rerun()

        return updated_segments

    def render_progress_bar(self, current: int, total: int, annotated: int):
        """渲染进度条"""
        progress = annotated / total if total > 0 else 0
        st.progress(progress, text=f"标注进度: {annotated}/{total} ({progress * 100:.1f}%)")

    def render_annotation_interface(self, video_index: int):
        """
        渲染完整的标注界面
        """
        video_path = self.data_manager.get_video_path(video_index)

        if not video_path:
            st.error("视频不存在")
            return

        # 加载标注数据
        annotation_data = self.data_manager.load_annotation(video_path)

        # 显示视频信息
        st.markdown(f"### 视频: {annotation_data['video_name']}")
        st.markdown(f"**时长:** {self.format_time(annotation_data['duration'])}")

        # 进度条
        total_videos = self.data_manager.get_video_count()
        annotated_count = self.data_manager.get_annotated_count()
        self.render_progress_bar(video_index + 1, total_videos, annotated_count)

        st.markdown("---")

        # 两列布局
        col_video, col_annotation = st.columns([1, 1])

        with col_video:
            # 视频播放器
            self.render_video_player(video_path)

        with col_annotation:
            # 添加新片段
            new_segment = self.render_segment_input(annotation_data['duration'])

            if new_segment:
                annotation_data['segments'].append(new_segment)
                annotation_data['annotated'] = True
                self.data_manager.save_annotation(video_path, annotation_data)
                st.success("✅ 片段已添加")
                st.rerun()

        st.markdown("---")

        # 片段列表
        updated_segments = self.render_segment_list(
            annotation_data['segments'],
            annotation_data
        )

        # 如果片段列表有更新，保存
        if updated_segments != annotation_data['segments']:
            annotation_data['segments'] = updated_segments
            annotation_data['annotated'] = len(updated_segments) > 0
            self.data_manager.save_annotation(video_path, annotation_data)
            st.rerun()

        st.markdown("---")

        # 底部操作栏
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            if st.button("💾 保存当前标注", type="primary"):
                annotation_data['annotated'] = len(annotation_data['segments']) > 0
                if self.data_manager.save_annotation(video_path, annotation_data):
                    st.success("✅ 标注已保存")

        with col2:
            if st.button("⏭️ 下一个视频"):
                if video_index < total_videos - 1:
                    st.session_state['video_index'] = video_index + 1
                    st.rerun()
                else:
                    st.info("已经是最后一个视频了")

        with col3:
            if st.button("⏮️ 上一个视频"):
                if video_index > 0:
                    st.session_state['video_index'] = video_index - 1
                    st.rerun()
                else:
                    st.info("已经是第一个视频了")