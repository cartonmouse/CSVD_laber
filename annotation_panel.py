"""
标注面板：负责片段标注的输入和管理
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QTextEdit, QPushButton, QListWidget,
                             QGroupBox, QMessageBox, QInputDialog, QListWidgetItem,
                             QScrollArea, QComboBox)
from PyQt5.QtCore import Qt, pyqtSignal
from typing import List, Dict


class AnnotationPanel(QWidget):
    """标注面板组件"""

    # 信号：片段被添加
    segment_added = pyqtSignal(dict)

    # 信号：片段被删除
    segment_deleted = pyqtSignal(int)

    # 信号：片段被修改
    segment_modified = pyqtSignal(int, dict)

    # 信号：请求跳转到时间
    seek_to_time = pyqtSignal(float)

    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.current_video_duration = 0.0
        self.segments = []


        self.noun_list = []
        self.verb_list = []
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()

        # 新片段输入区域
        input_group = self.create_input_group()
        layout.addWidget(input_group)

        # 片段列表区域
        list_group = self.create_segment_list_group()
        layout.addWidget(list_group)

        self.setLayout(layout)

    def create_input_group(self) -> QGroupBox:
        """创建输入区域"""
        group = QGroupBox("添加新片段")
        layout = QVBoxLayout()

        # 时间输入
        time_layout = QHBoxLayout()

        time_layout.addWidget(QLabel("开始时间:"))
        self.start_time_input = QLineEdit()
        self.start_time_input.setPlaceholderText("MM:SS.mmm")
        self.start_time_input.setText("00:00.000")
        time_layout.addWidget(self.start_time_input)

        time_layout.addWidget(QLabel("结束时间:"))
        self.end_time_input = QLineEdit()
        self.end_time_input.setPlaceholderText("MM:SS.mmm")
        self.end_time_input.setText("00:00.000")
        time_layout.addWidget(self.end_time_input)

        layout.addLayout(time_layout)

        # 描述输入
        layout.addWidget(QLabel("描述:"))
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("描述这个片段中发生的事情...")
        self.description_input.setMaximumHeight(80)
        layout.addWidget(self.description_input)

        # 在第70行左右，description_input之后添加：

        # 动词输入（可下拉选择或自定义）
        verb_layout = QHBoxLayout()
        verb_layout.addWidget(QLabel("动词:"))
        self.verb_combo = QComboBox()
        self.verb_combo.setEditable(True)
        self.verb_combo.setPlaceholderText("选择或输入动词")
        verb_layout.addWidget(self.verb_combo, 3)

        self.add_verb_button = QPushButton("+ 保存")
        self.add_verb_button.clicked.connect(self.add_custom_verb)
        self.add_verb_button.setMaximumWidth(60)
        verb_layout.addWidget(self.add_verb_button)

        layout.addLayout(verb_layout)

        # 名词输入（可下拉选择或自定义）
        noun_layout = QHBoxLayout()
        noun_layout.addWidget(QLabel("名词:"))
        self.noun_combo = QComboBox()
        self.noun_combo.setEditable(True)
        self.noun_combo.setPlaceholderText("选择或输入名词")
        noun_layout.addWidget(self.noun_combo, 3)

        self.add_noun_button = QPushButton("+ 保存")
        self.add_noun_button.clicked.connect(self.add_custom_noun)
        self.add_noun_button.setMaximumWidth(60)
        noun_layout.addWidget(self.add_noun_button)

        layout.addLayout(noun_layout)


        # 新增：标签管理按钮
        manage_layout = QHBoxLayout()
        manage_layout.addStretch()
        self.manage_tags_button = QPushButton("📝 管理标签库")
        self.manage_tags_button.clicked.connect(self.open_tag_manager)
        manage_layout.addWidget(self.manage_tags_button)
        layout.addLayout(manage_layout)

        # 添加按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.add_segment_button = QPushButton("添加片段")
        self.add_segment_button.clicked.connect(self.add_segment)
        self.add_segment_button.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; padding: 8px; }"
        )
        button_layout.addWidget(self.add_segment_button)

        layout.addLayout(button_layout)

        group.setLayout(layout)
        return group

    def create_segment_list_group(self) -> QGroupBox:
        """创建片段列表区域"""
        group = QGroupBox("已标注片段")
        layout = QVBoxLayout()

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        self.segment_list_widget = QWidget()
        self.segment_list_layout = QVBoxLayout()
        self.segment_list_widget.setLayout(self.segment_list_layout)

        scroll.setWidget(self.segment_list_widget)
        layout.addWidget(scroll)

        group.setLayout(layout)
        return group



    def parse_time(self, time_str: str) -> float:
        """解析时间字符串为秒数"""
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

    def format_time(self, seconds: float) -> str:
        """格式化时间为 MM:SS.mmm"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds - int(seconds)) * 1000)
        return f"{minutes:02d}:{secs:02d}.{milliseconds:03d}"

    def add_segment(self):
        """添加新片段"""
        # 解析时间
        start_time = self.parse_time(self.start_time_input.text())
        end_time = self.parse_time(self.end_time_input.text())

        # 验证时间
        if start_time is None or end_time is None:
            QMessageBox.warning(self, "错误", "时间格式错误，请使用 MM:SS.mmm 格式")
            return

        if start_time >= end_time:
            QMessageBox.warning(self, "错误", "开始时间必须小于结束时间")
            return

        if end_time > self.current_video_duration:
            QMessageBox.warning(
                self, "错误",
                f"结束时间超出视频时长 ({self.format_time(self.current_video_duration)})"
            )
            return

        # 获取描述
        description = self.description_input.toPlainText().strip()

        # 获取名词和动词
        noun = self.noun_combo.currentText().strip()
        verb = self.verb_combo.currentText().strip()

        # 创建片段
        segment = self.data_manager.create_segment(
            start_time=start_time,
            end_time=end_time,
            description=description,
            tags=[]
        )

        # 添加名词和动词
        segment['noun'] = noun
        segment['verb'] = verb

        # 发送信号
        self.segment_added.emit(segment)

        # 清空输入
        self.description_input.clear()
        self.noun_combo.setCurrentText("")
        self.verb_combo.setCurrentText("")

        QMessageBox.information(self, "成功", "片段已添加")

    def load_segments(self, segments: List[Dict]):
        """加载片段列表"""
        self.segments = segments
        self.refresh_segment_list()

    def refresh_segment_list(self):
        """刷新片段列表显示"""
        # 清空现有列表
        while self.segment_list_layout.count():
            child = self.segment_list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # 添加片段
        for idx, segment in enumerate(self.segments):
            segment_widget = self.create_segment_widget(idx, segment)
            self.segment_list_layout.addWidget(segment_widget)

        # 添加弹性空间
        self.segment_list_layout.addStretch()

    def create_segment_widget(self, index: int, segment: Dict) -> QGroupBox:
        """创建单个片段的显示组件"""
        group = QGroupBox(f"片段 {index + 1}")
        layout = QVBoxLayout()

        # 时间信息
        time_text = (f"时间: {self.format_time(segment['start_time'])} - "
                     f"{self.format_time(segment['end_time'])} "
                     f"(时长: {self.format_time(segment['end_time'] - segment['start_time'])})")
        time_label = QLabel(time_text)
        layout.addWidget(time_label)

        # 描述
        desc_text = segment['description'] if segment['description'] else "(无描述)"
        desc_label = QLabel(f"描述: {desc_text}")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # 名词
        noun_text = segment.get('noun', '') or "(无)"
        noun_label = QLabel(f"名词: {noun_text}")
        layout.addWidget(noun_label)

        # 动词
        verb_text = segment.get('verb', '') or "(无)"
        verb_label = QLabel(f"动词: {verb_text}")
        layout.addWidget(verb_label)


        # 按钮
        button_layout = QHBoxLayout()

        jump_button = QPushButton("跳转")
        jump_button.clicked.connect(lambda: self.jump_to_segment(segment))
        button_layout.addWidget(jump_button)

        delete_button = QPushButton("删除")
        delete_button.clicked.connect(lambda: self.delete_segment(index))
        delete_button.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")
        button_layout.addWidget(delete_button)

        button_layout.addStretch()

        layout.addLayout(button_layout)

        group.setLayout(layout)
        return group

    def jump_to_segment(self, segment: Dict):
        """跳转到片段开始时间"""
        self.seek_to_time.emit(segment['start_time'])

    def delete_segment(self, index: int):
        """删除片段"""
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除片段 {index + 1} 吗？",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.segment_deleted.emit(index)

    def set_video_duration(self, duration: float):
        """设置当前视频时长"""
        self.current_video_duration = duration

    def set_current_time(self, time_seconds: float):
        """设置当前时间到开始时间输入框"""
        self.start_time_input.setText(self.format_time(time_seconds))

    def set_start_time_from_current(self, time_seconds: float):
        """从当前播放位置设置开始时间"""
        self.start_time_input.setText(self.format_time(time_seconds))

    def set_end_time_from_current(self, time_seconds: float):
        """从当前播放位置设置结束时间"""
        self.end_time_input.setText(self.format_time(time_seconds))

    def add_custom_noun(self):
        """添加自定义名词到列表"""
        noun = self.noun_combo.currentText().strip()
        if noun and noun not in self.noun_list:
            self.noun_list.append(noun)
            self.update_combo_boxes()
            self.noun_combo.setCurrentText(noun)

    def add_custom_verb(self):
        """添加自定义动词到列表"""
        verb = self.verb_combo.currentText().strip()
        if verb and verb not in self.verb_list:
            self.verb_list.append(verb)
            self.update_combo_boxes()
            self.verb_combo.setCurrentText(verb)

    def get_noun_verb_lists(self):
        """获取名词和动词列表"""
        return self.noun_list.copy(), self.verb_list.copy()

    def set_noun_verb_lists(self, nouns, verbs):
        """设置名词和动词列表"""
        self.noun_list = nouns
        self.verb_list = verbs
        self.noun_combo.clear()
        self.noun_combo.addItems(self.noun_list)
        self.verb_combo.clear()
        self.verb_combo.addItems(self.verb_list)

    def open_tag_manager(self):
        """打开标签管理对话框"""
        from PyQt5.QtWidgets import QDialog, QListWidget, QVBoxLayout, QHBoxLayout, QPushButton, QInputDialog

        dialog = QDialog(self)
        dialog.setWindowTitle("标签管理")
        dialog.setMinimumWidth(500)
        dialog.setMinimumHeight(400)

        layout = QVBoxLayout()

        # 名词标签管理
        layout.addWidget(QLabel("名词标签:"))
        noun_list_widget = QListWidget()
        noun_list_widget.addItems(self.noun_list)
        layout.addWidget(noun_list_widget)

        noun_button_layout = QHBoxLayout()
        add_noun_btn = QPushButton("+ 添加名词")
        add_noun_btn.clicked.connect(lambda: self.add_tag_in_manager(noun_list_widget, self.noun_list, "名词"))
        noun_button_layout.addWidget(add_noun_btn)

        delete_noun_btn = QPushButton("- 删除选中")
        delete_noun_btn.clicked.connect(lambda: self.delete_tag_in_manager(noun_list_widget, self.noun_list))
        noun_button_layout.addWidget(delete_noun_btn)

        up_noun_btn = QPushButton("↑ 上移")
        up_noun_btn.clicked.connect(lambda: self.move_tag_up(noun_list_widget, self.noun_list))
        noun_button_layout.addWidget(up_noun_btn)

        down_noun_btn = QPushButton("↓ 下移")
        down_noun_btn.clicked.connect(lambda: self.move_tag_down(noun_list_widget, self.noun_list))
        noun_button_layout.addWidget(down_noun_btn)

        layout.addLayout(noun_button_layout)

        # 动词标签管理
        layout.addWidget(QLabel("动词标签:"))
        verb_list_widget = QListWidget()
        verb_list_widget.addItems(self.verb_list)
        layout.addWidget(verb_list_widget)

        verb_button_layout = QHBoxLayout()
        add_verb_btn = QPushButton("+ 添加动词")
        add_verb_btn.clicked.connect(lambda: self.add_tag_in_manager(verb_list_widget, self.verb_list, "动词"))
        verb_button_layout.addWidget(add_verb_btn)

        delete_verb_btn = QPushButton("- 删除选中")
        delete_verb_btn.clicked.connect(lambda: self.delete_tag_in_manager(verb_list_widget, self.verb_list))
        verb_button_layout.addWidget(delete_verb_btn)

        up_verb_btn = QPushButton("↑ 上移")
        up_verb_btn.clicked.connect(lambda: self.move_tag_up(verb_list_widget, self.verb_list))
        verb_button_layout.addWidget(up_verb_btn)

        down_verb_btn = QPushButton("↓ 下移")
        down_verb_btn.clicked.connect(lambda: self.move_tag_down(verb_list_widget, self.verb_list))
        verb_button_layout.addWidget(down_verb_btn)

        layout.addLayout(verb_button_layout)

        # 关闭按钮
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_btn = QPushButton("完成")
        close_btn.clicked.connect(dialog.accept)
        close_layout.addWidget(close_btn)
        layout.addLayout(close_layout)

        dialog.setLayout(layout)
        dialog.exec_()

        # 更新下拉框
        self.update_combo_boxes()

    def add_tag_in_manager(self, list_widget, tag_list, tag_type):
        """在管理器中添加标签"""
        from PyQt5.QtWidgets import QInputDialog
        tag, ok = QInputDialog.getText(self, f"添加{tag_type}", f"{tag_type}名称:")
        if ok and tag:
            tag = tag.strip()
            if tag and tag not in tag_list:
                tag_list.append(tag)
                list_widget.addItem(tag)

    def delete_tag_in_manager(self, list_widget, tag_list):
        """在管理器中删除标签"""
        current_item = list_widget.currentItem()
        if current_item:
            tag = current_item.text()
            reply = QMessageBox.question(
                self, "确认删除",
                f"确定要删除标签 '{tag}' 吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                tag_list.remove(tag)
                list_widget.takeItem(list_widget.row(current_item))

    def move_tag_up(self, list_widget, tag_list):
        """上移标签"""
        current_row = list_widget.currentRow()
        if current_row > 0:
            tag_list[current_row], tag_list[current_row - 1] = tag_list[current_row - 1], tag_list[current_row]
            current_item = list_widget.takeItem(current_row)
            list_widget.insertItem(current_row - 1, current_item)
            list_widget.setCurrentRow(current_row - 1)

    def move_tag_down(self, list_widget, tag_list):
        """下移标签"""
        current_row = list_widget.currentRow()
        if current_row < list_widget.count() - 1:
            tag_list[current_row], tag_list[current_row + 1] = tag_list[current_row + 1], tag_list[current_row]
            current_item = list_widget.takeItem(current_row)
            list_widget.insertItem(current_row + 1, current_item)
            list_widget.setCurrentRow(current_row + 1)

    def update_combo_boxes(self):
        """更新名词和动词下拉框"""
        # 保存当前选择
        current_noun = self.noun_combo.currentText()
        current_verb = self.verb_combo.currentText()

        # 更新名词下拉框
        self.noun_combo.clear()
        self.noun_combo.addItems(self.noun_list)
        if current_noun in self.noun_list:
            self.noun_combo.setCurrentText(current_noun)

        # 更新动词下拉框
        self.verb_combo.clear()
        self.verb_combo.addItems(self.verb_list)
        if current_verb in self.verb_list:
            self.verb_combo.setCurrentText(current_verb)

    def focus_description_input(self):
        """将焦点设置到描述输入框"""
        self.description_input.setFocus()

    def quick_select_tag(self, num: int):
        """
        快速选择第num个标签
        num为1-9，对应名词或动词列表的前9个
        逻辑：
        - 如果名词未选择，选择第num个名词
        - 如果名词已选择，选择第num个动词
        """
        # 检查名词是否已选择
        current_noun = self.noun_combo.currentText().strip()

        if not current_noun:
            # 名词未选择，选择名词
            if num <= len(self.noun_list):
                self.noun_combo.setCurrentIndex(num - 1)
        else:
            # 名词已选择，选择动词
            if num <= len(self.verb_list):
                self.verb_combo.setCurrentIndex(num - 1)