"""
主程序：Streamlit视频标注工具
"""

import streamlit as st
from data_manager import DataManager
from video_annotator import VideoAnnotator
from config import init_directories, VIDEO_DIR, EXPORT_JSON


def init_session_state():
    """初始化session state"""
    if 'video_index' not in st.session_state:
        st.session_state['video_index'] = 0
    if 'data_manager' not in st.session_state:
        st.session_state['data_manager'] = DataManager()
    if 'annotator' not in st.session_state:
        st.session_state['annotator'] = VideoAnnotator(
            st.session_state['data_manager']
        )


def render_sidebar():
    """渲染侧边栏"""
    st.sidebar.title("🏗️ 建筑工地视频标注工具")

    data_manager = st.session_state['data_manager']

    # 统计信息
    st.sidebar.markdown("### 📊 数据统计")
    total_videos = data_manager.get_video_count()
    annotated_count = data_manager.get_annotated_count()

    st.sidebar.metric("视频总数", total_videos)
    st.sidebar.metric("已标注", annotated_count)
    st.sidebar.metric("未标注", total_videos - annotated_count)

    if total_videos > 0:
        progress = annotated_count / total_videos
        st.sidebar.progress(progress)
        st.sidebar.caption(f"完成度: {progress * 100:.1f}%")

    st.sidebar.markdown("---")

    # 视频选择
    st.sidebar.markdown("### 🎬 视频导航")

    if total_videos > 0:
        current_index = st.session_state['video_index']

        # 视频选择器
        new_index = st.sidebar.selectbox(
            "选择视频",
            range(total_videos),
            index=current_index,
            format_func=lambda x: f"{x+1}. {data_manager.get_video_display_name(data_manager.get_video_path(x))}"

        )

        if new_index != current_index:
            st.session_state['video_index'] = new_index
            st.rerun()

        # 快速跳转按钮
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("⏮️ 首个", use_container_width=True):
                st.session_state['video_index'] = 0
                st.rerun()
        with col2:
            if st.button("⏭️ 末个", use_container_width=True):
                st.session_state['video_index'] = total_videos - 1
                st.rerun()
    else:
        st.sidebar.warning(f"未找到视频文件\n请检查路径: {VIDEO_DIR}")

    st.sidebar.markdown("---")

    # 数据管理
    st.sidebar.markdown("### 💾 数据管理")

    if st.sidebar.button("🔄 刷新视频列表", use_container_width=True):
        data_manager.load_video_list()
        st.sidebar.success("✅ 已刷新")
        st.rerun()

    if st.sidebar.button("📤 导出所有标注", use_container_width=True):
        if data_manager.export_all_annotations():
            st.sidebar.success(f"✅ 已导出到:\n{EXPORT_JSON}")
        else:
            st.sidebar.error("❌ 导出失败")

    st.sidebar.markdown("---")

    # 当前标签列表
    with st.sidebar.expander("🏷️ 查看所有标签"):
        tags = data_manager.get_tags()
        for tag in tags:
            st.sidebar.markdown(f"- {tag}")
        st.sidebar.caption(f"共 {len(tags)} 个标签")


def render_main_content():
    """渲染主内容区"""
    data_manager = st.session_state['data_manager']
    annotator = st.session_state['annotator']

    total_videos = data_manager.get_video_count()

    if total_videos == 0:
        st.warning(f"⚠️ 未找到视频文件，请检查视频目录: {VIDEO_DIR}")
        st.info("""
        **使用说明:**
        1. 将视频文件放入配置的VIDEO_DIR目录
        2. 点击侧边栏的"刷新视频列表"按钮
        3. 开始标注
        """)
        return

    # 渲染标注界面
    current_index = st.session_state['video_index']
    annotator.render_annotation_interface(current_index)


def main():
    """主函数"""
    # 页面配置
    st.set_page_config(
        page_title="视频标注工具",
        page_icon="🏗️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # 初始化目录
    init_directories()

    # 初始化session state
    init_session_state()

    # 渲染界面
    render_sidebar()
    render_main_content()

    # 页脚
    st.markdown("---")
    st.caption("🏗️ 建筑工地视频标注工具 | 使用Streamlit构建")


if __name__ == "__main__":
    main()