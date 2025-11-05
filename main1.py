"""
主窗口：整合所有组件的主程序
"""

import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QPushButton, QComboBox,
                             QGroupBox, QMessageBox, QProgressBar, QSplitter,
                             QDialog, QListWidget, QDialogButtonBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from config import WINDOW_WIDTH, WINDOW_HEIGHT, init_directories, EXPORT_JSON, VIDEO_DIR

from config import WINDOW_WIDTH, WINDOW_HEIGHT, init_directories, EXPORT_JSON
from data_manager import DataManager
from video_player import VideoPlayer
from annotation_panel import AnnotationPanel


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.data_manager = DataManager()
        self.current_video_index = 0
        self.current_annotation = None

        init_directories()

        # 新增：启动时选择子文件夹
        if not self.select_subfolder_on_startup():
            sys.exit()  # 如果用户取消选择，退出程序

        self.init_ui()

        # 新增：在加载视频前先加载标签缓存
        noun_list, verb_list = self.load_noun_verb_cache()
        self.annotation_panel.set_noun_verb_lists(noun_list, verb_list)

        self.load_first_video()
        self.setup_shortcuts()

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("建筑工地视频标注工具")
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)

        # 中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()

        # 顶部工具栏
        toolbar = self.create_toolbar()
        main_layout.addWidget(toolbar)

        # 主内容区域（视频播放器 + 标注面板）
        content_splitter = QSplitter(Qt.Horizontal)

        # 左侧：视频播放器
        self.video_player = VideoPlayer()
        self.video_player.position_changed.connect(self.on_position_changed)
        self.video_player.video_loaded.connect(self.on_video_loaded)
        content_splitter.addWidget(self.video_player)

        # 右侧：标注面板
        self.annotation_panel = AnnotationPanel(self.data_manager)
        self.annotation_panel.segment_added.connect(self.on_segment_added)
        self.annotation_panel.segment_deleted.connect(self.on_segment_deleted)
        self.annotation_panel.seek_to_time.connect(self.video_player.seek_to_time)
        content_splitter.addWidget(self.annotation_panel)

        # 设置分割比例
        content_splitter.setStretchFactor(0, 6)
        content_splitter.setStretchFactor(1, 4)

        main_layout.addWidget(content_splitter)

        # 底部状态栏
        status_bar = self.create_status_bar()
        main_layout.addWidget(status_bar)

        central_widget.setLayout(main_layout)

    def setup_shortcuts(self):
        """设置快捷键"""
        from PyQt5.QtWidgets import QShortcut
        from PyQt5.QtGui import QKeySequence

        # Q键：设置开始时间
        shortcut_start = QShortcut(QKeySequence('Q'), self)
        shortcut_start.activated.connect(self.set_start_time_from_player)

        # E键：设置结束时间
        shortcut_end = QShortcut(QKeySequence('E'), self)
        shortcut_end.activated.connect(self.set_end_time_from_player)

        # S键：播放/暂停
        shortcut_play = QShortcut(QKeySequence('S'), self)
        shortcut_play.activated.connect(self.toggle_play_pause)

    def set_start_time_from_player(self):
        """从当前播放位置设置开始时间"""
        current_time = self.video_player.get_current_time()
        self.annotation_panel.set_start_time_from_current(current_time)

    def set_end_time_from_player(self):
        """从当前播放位置设置结束时间"""
        current_time = self.video_player.get_current_time()
        self.annotation_panel.set_end_time_from_current(current_time)

    def toggle_play_pause(self):
        """切换播放/暂停状态"""
        self.video_player.toggle_play()

    def create_toolbar(self) -> QGroupBox:
        """创建顶部工具栏"""
        group = QGroupBox("视频导航与控制")
        group.setMaximumHeight(80)  # 新增：限制高度
        layout = QHBoxLayout()

        # 视频选择下拉框
        layout.addWidget(QLabel("视频:"))
        self.video_selector = QComboBox()
        self.video_selector.currentIndexChanged.connect(self.on_video_changed)
        self.update_video_selector()
        layout.addWidget(self.video_selector, 2)  # 新增：拉伸因子

        # 导航按钮
        self.prev_button = QPushButton("⏮")  # 修改：简化文字
        self.prev_button.setMaximumWidth(40)  # 新增：限制宽度
        self.prev_button.clicked.connect(self.prev_video)
        layout.addWidget(self.prev_button)

        self.next_button = QPushButton("⏭")  # 修改：简化文字
        self.next_button.setMaximumWidth(40)  # 新增：限制宽度
        self.next_button.clicked.connect(self.next_video)
        layout.addWidget(self.next_button)

        # 保存和导出按钮
        self.save_button = QPushButton("💾 保存")  # 修改：简化文字
        self.save_button.setMaximumWidth(80)  # 新增：限制宽度
        self.save_button.clicked.connect(self.save_annotation)
        self.save_button.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; padding: 5px; }"  # 修改：padding改为5px
        )
        layout.addWidget(self.save_button)

        self.export_button = QPushButton("📤 导出")  # 修改：简化文字
        self.export_button.setMaximumWidth(80)  # 新增：限制宽度
        self.export_button.clicked.connect(self.export_all)
        self.export_button.setStyleSheet(
            "QPushButton { background-color: #FF9800; color: white; padding: 5px; }"  # 修改：padding改为5px
        )
        layout.addWidget(self.export_button)

        # 新增：切换文件夹按钮
        self.switch_folder_button = QPushButton("📁 切换文件夹")
        self.switch_folder_button.setMaximumWidth(100)
        self.switch_folder_button.clicked.connect(self.switch_subfolder)
        self.switch_folder_button.setStyleSheet(
            "QPushButton { background-color: #9C27B0; color: white; padding: 5px; }"
        )
        layout.addWidget(self.switch_folder_button)

        group.setLayout(layout)
        return group

        group.setLayout(layout)
        return group

    def create_status_bar(self) -> QWidget:
        """创建底部状态栏"""
        widget = QWidget()
        widget.setMaximumHeight(40)  # 新增：限制高度

        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)  # 新增：减小边距

        # 统计信息
        total_videos = self.data_manager.get_video_count()
        annotated_count = self.data_manager.get_annotated_count()

        self.status_label = QLabel(
            f"总: {total_videos} | 已标注: {annotated_count} | "  # 修改：简化文字
            f"未标注: {total_videos - annotated_count}"
        )
        self.status_label.setFont(QFont("Arial", 9))  # 修改：字体改小
        layout.addWidget(self.status_label)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(total_videos)
        self.progress_bar.setValue(annotated_count)
        self.progress_bar.setMaximumHeight(20)  # 新增：限制高度
        self.progress_bar.setMaximumWidth(200)  # 新增：限制宽度
        layout.addWidget(self.progress_bar)

        widget.setLayout(layout)
        return widget

    def update_video_selector(self):
        """更新视频选择下拉框"""
        self.video_selector.blockSignals(True)
        self.video_selector.clear()

        for i in range(self.data_manager.get_video_count()):
            video_path = self.data_manager.get_video_path(i)
            display_name = self.data_manager.get_video_display_name(video_path)
            self.video_selector.addItem(f"{i + 1}. {display_name}")

        self.video_selector.setCurrentIndex(self.current_video_index)
        self.video_selector.blockSignals(False)

    def update_status_bar(self):
        """更新状态栏"""
        total_videos = self.data_manager.get_video_count()
        annotated_count = self.data_manager.get_annotated_count()

        self.status_label.setText(
            f"总视频数: {total_videos} | 已标注: {annotated_count} | "
            f"未标注: {total_videos - annotated_count}"
        )
        self.progress_bar.setValue(annotated_count)

    def load_first_video(self):
        """加载第一个视频"""
        if self.data_manager.get_video_count() > 0:
            self.load_video(0)
        else:
            QMessageBox.warning(
                self, "警告",
                f"未找到视频文件\n请检查配置的视频目录"
            )

    def load_video(self, index: int):
        """加载指定索引的视频"""
        video_path = self.data_manager.get_video_path(index)
        if not video_path:
            return

        # 加载视频
        if not self.video_player.load_video(video_path):
            QMessageBox.critical(self, "错误", f"无法加载视频: {video_path}")
            return

        # 加载标注数据
        self.current_annotation = self.data_manager.load_annotation(video_path)
        self.annotation_panel.load_segments(self.current_annotation['segments'])

        # 更新索引
        self.current_video_index = index
        self.video_selector.setCurrentIndex(index)

        # 更新窗口标题
        display_name = self.data_manager.get_video_display_name(video_path)
        current_subfolder = self.data_manager.get_current_subfolder()
        if current_subfolder:
            folder_name = self.data_manager.get_subfolder_display_name(current_subfolder)
            self.setWindowTitle(f"建筑工地视频标注工具 - [{folder_name}] {display_name}")
        else:
            self.setWindowTitle(f"建筑工地视频标注工具 - {display_name}")


    def on_video_changed(self, index: int):
        """视频选择改变"""
        if index >= 0 and index != self.current_video_index:
            # 保存当前标注
            self.save_annotation(silent=True)
            # 加载新视频
            self.load_video(index)

    def prev_video(self):
        """上一个视频"""
        if self.current_video_index > 0:
            self.save_annotation(silent=True)
            self.load_video(self.current_video_index - 1)

    def next_video(self):
        """下一个视频"""
        if self.current_video_index < self.data_manager.get_video_count() - 1:
            self.save_annotation(silent=True)
            self.load_video(self.current_video_index + 1)

    def on_video_loaded(self, duration: float):
        """视频加载完成"""
        self.annotation_panel.set_video_duration(duration)

    def on_position_changed(self, time_seconds: float):
        """播放位置改变"""
        # 可以在这里添加实时更新标注输入框的逻辑
        pass

    def on_segment_added(self, segment: dict):
        """片段被添加"""
        self.current_annotation['segments'].append(segment)
        self.current_annotation['annotated'] = True
        self.annotation_panel.load_segments(self.current_annotation['segments'])
        self.save_annotation(silent=True)
        self.save_noun_verb_cache()  # 新增：每次添加片段时保存标签缓存

    def on_segment_deleted(self, index: int):
        """片段被删除"""
        if 0 <= index < len(self.current_annotation['segments']):
            self.current_annotation['segments'].pop(index)
            self.current_annotation['annotated'] = len(self.current_annotation['segments']) > 0
            self.annotation_panel.load_segments(self.current_annotation['segments'])
            self.save_annotation(silent=True)

    def save_annotation(self, silent=False):
        """保存当前标注"""
        if not self.current_annotation:
            return

        video_path = self.data_manager.get_video_path(self.current_video_index)
        if self.data_manager.save_annotation(video_path, self.current_annotation):
            if not silent:
                QMessageBox.information(self, "成功", "标注已保存")
            self.update_status_bar()
        else:
            if not silent:
                QMessageBox.critical(self, "错误", "保存失败")

    def export_all(self):
        """导出所有标注"""
        if self.data_manager.export_all_annotations():
            QMessageBox.information(
                self, "成功",
                f"所有标注已导出到:\n{EXPORT_JSON}"  # 修改：使用导入的EXPORT_JSON
            )
        else:
            QMessageBox.critical(self, "错误", "导出失败")

    def save_noun_verb_cache(self):
        """保存名词和动词列表到缓存"""
        import json
        nouns, verbs = self.annotation_panel.get_noun_verb_lists()
        cache = {'nouns': nouns, 'verbs': verbs}
        try:
            with open('./noun_verb_cache.json', 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
        except:
            pass

    def load_noun_verb_cache(self):
        """加载名词和动词列表缓存"""
        import json
        try:
            with open('./noun_verb_cache.json', 'r', encoding='utf-8') as f:
                cache = json.load(f)
                return cache.get('nouns', []), cache.get('verbs', [])
        except:
            return [], []

    def select_subfolder_on_startup(self) -> bool:
        """
        启动时选择子文件夹
        返回True表示选择成功，False表示用户取消
        """
        subfolders = self.data_manager.get_subfolders()

        if not subfolders:
            QMessageBox.critical(
                None, "错误",
                f"在以下目录未找到任何子文件夹:\n{VIDEO_DIR}\n\n"
                f"请检查配置文件中的VIDEO_DIR路径"
            )
            return False

        # 创建选择对话框
        dialog = QDialog()
        dialog.setWindowTitle("选择要标注的文件夹")
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(400)

        layout = QVBoxLayout()

        # 说明文字
        info_label = QLabel(f"请选择要标注的子文件夹:\n根目录: {VIDEO_DIR}")
        layout.addWidget(info_label)

        # 文件夹列表
        list_widget = QListWidget()
        for subfolder in subfolders:
            display_name = self.data_manager.get_subfolder_display_name(subfolder)
            video_count = self.data_manager.get_video_count_in_subfolder(subfolder)
            list_widget.addItem(f"{display_name} ({video_count} 个视频)")

        list_widget.setCurrentRow(0)  # 默认选中第一个
        layout.addWidget(list_widget)

        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.setLayout(layout)

        # 显示对话框
        if dialog.exec_() == QDialog.Accepted:
            selected_index = list_widget.currentRow()
            if selected_index >= 0:
                selected_subfolder = subfolders[selected_index]
                self.data_manager.load_videos_from_subfolder(selected_subfolder)
                return True

        return False

    def switch_subfolder(self):
        """
        切换到另一个子文件夹
        """
        # 保存当前标注
        self.save_annotation(silent=True)

        subfolders = self.data_manager.get_subfolders()

        if not subfolders:
            QMessageBox.warning(
                self, "错误",
                f"未找到任何子文件夹"
            )
            return

        # 获取当前子文件夹
        current_subfolder = self.data_manager.get_current_subfolder()
        current_index = 0
        if current_subfolder and current_subfolder in subfolders:
            current_index = subfolders.index(current_subfolder)

        # 创建选择对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("切换文件夹")
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(400)

        layout = QVBoxLayout()

        # 说明文字
        if current_subfolder:
            current_name = self.data_manager.get_subfolder_display_name(current_subfolder)
            info_label = QLabel(f"当前文件夹: {current_name}\n\n请选择要切换到的子文件夹:")
        else:
            info_label = QLabel("请选择要标注的子文件夹:")
        layout.addWidget(info_label)

        # 文件夹列表
        list_widget = QListWidget()
        for subfolder in subfolders:
            display_name = self.data_manager.get_subfolder_display_name(subfolder)
            video_count = self.data_manager.get_video_count_in_subfolder(subfolder)
            list_widget.addItem(f"{display_name} ({video_count} 个视频)")

        list_widget.setCurrentRow(current_index)  # 默认选中当前文件夹
        layout.addWidget(list_widget)

        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.setLayout(layout)

        # 显示对话框
        if dialog.exec_() == QDialog.Accepted:
            selected_index = list_widget.currentRow()
            if selected_index >= 0:
                selected_subfolder = subfolders[selected_index]

                # 如果选择的是当前文件夹，不做任何操作
                if selected_subfolder == current_subfolder:
                    QMessageBox.information(self, "提示", "您选择的是当前文件夹")
                    return

                # 切换到新文件夹
                self.data_manager.load_videos_from_subfolder(selected_subfolder)

                # 重新加载界面
                self.current_video_index = 0
                self.update_video_selector()
                self.update_status_bar()
                self.load_first_video()

                folder_name = self.data_manager.get_subfolder_display_name(selected_subfolder)
                QMessageBox.information(
                    self, "成功",
                    f"已切换到文件夹: {folder_name}\n视频数量: {self.data_manager.get_video_count()}"
                )

    def closeEvent(self, event):
        """关闭窗口前保存"""
        self.save_annotation(silent=True)
        self.save_noun_verb_cache()  # 新增：保存名词动词缓存
        event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()