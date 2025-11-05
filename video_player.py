"""
视频播放器组件：使用OpenCV和PyQt5实现
"""

import cv2
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QSlider)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from config import VIDEO_WIDTH, VIDEO_HEIGHT


class VideoPlayer(QWidget):
    """视频播放器组件"""

    # 信号：当前播放位置改变（秒）
    position_changed = pyqtSignal(float)

    # 信号：视频加载完成（总时长）
    video_loaded = pyqtSignal(float)

    def __init__(self):
        super().__init__()
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        self.is_playing = False
        self.total_frames = 0
        self.fps = 0
        self.duration = 0.0
        self.current_frame = 0

        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()

        # 视频显示区域
        self.video_label = QLabel()
        self.video_label.setFixedSize(VIDEO_WIDTH, VIDEO_HEIGHT)
        self.video_label.setStyleSheet("background-color: black;")
        self.video_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.video_label)

        # 时间显示
        time_layout = QHBoxLayout()
        self.time_label = QLabel("00:00.000 / 00:00.000")
        time_layout.addWidget(self.time_label)
        layout.addLayout(time_layout)

        # 进度条
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(1000)
        self.slider.setValue(0)
        self.slider.sliderMoved.connect(self.on_slider_moved)
        self.slider.sliderPressed.connect(self.on_slider_pressed)
        self.slider.sliderReleased.connect(self.on_slider_released)
        layout.addWidget(self.slider)

        # 控制按钮
        control_layout = QHBoxLayout()

        self.play_button = QPushButton("播放")
        self.play_button.clicked.connect(self.toggle_play)
        control_layout.addWidget(self.play_button)

        self.stop_button = QPushButton("停止")
        self.stop_button.clicked.connect(self.stop)
        control_layout.addWidget(self.stop_button)

        control_layout.addStretch()

        layout.addLayout(control_layout)

        self.setLayout(layout)

    def load_video(self, video_path: str) -> bool:
        """加载视频文件"""
        # 释放之前的视频
        if self.cap:
            self.cap.release()

        self.cap = cv2.VideoCapture(video_path)

        if not self.cap.isOpened():
            print(f"无法打开视频: {video_path}")
            return False

        # 获取视频信息
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.duration = self.total_frames / self.fps if self.fps > 0 else 0
        self.current_frame = 0

        # 显示第一帧
        self.show_frame(0)

        # 更新UI
        self.update_time_label()
        self.slider.setValue(0)

        # 发送信号
        self.video_loaded.emit(self.duration)

        return True

    def show_frame(self, frame_number: int):
        """显示指定帧"""
        if not self.cap:
            return

        # 设置帧位置
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = self.cap.read()

        if ret:
            self.current_frame = frame_number

            # 转换为Qt格式
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)

            # 缩放到显示区域
            pixmap = QPixmap.fromImage(qt_image)
            scaled_pixmap = pixmap.scaled(
                VIDEO_WIDTH, VIDEO_HEIGHT,
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )

            self.video_label.setPixmap(scaled_pixmap)

            # 更新时间和进度条
            self.update_time_label()
            self.update_slider()

            # 发送位置信号
            current_time = self.get_current_time()
            self.position_changed.emit(current_time)

    def update_frame(self):
        """定时器回调：播放下一帧"""
        if not self.cap or not self.is_playing:
            return

        next_frame = self.current_frame + 1

        if next_frame >= self.total_frames:
            # 播放结束
            self.stop()
            return

        self.show_frame(next_frame)

    def toggle_play(self):
        """切换播放/暂停"""
        if self.is_playing:
            self.pause()
        else:
            self.play()

    def play(self):
        """开始播放"""
        if not self.cap:
            return

        self.is_playing = True
        self.play_button.setText("暂停")

        # 启动定时器，间隔为帧间隔时间
        interval = int(1000 / self.fps) if self.fps > 0 else 30
        self.timer.start(interval)

    def pause(self):
        """暂停播放"""
        self.is_playing = False
        self.play_button.setText("播放")
        self.timer.stop()

    def stop(self):
        """停止播放并回到开始"""
        self.pause()
        self.show_frame(0)

    def on_slider_pressed(self):
        """进度条按下时暂停播放"""
        if self.is_playing:
            self.was_playing = True
            self.pause()
        else:
            self.was_playing = False

    def on_slider_moved(self, value):
        """进度条拖动"""
        if not self.cap:
            return

        # 计算对应的帧号
        frame_number = int((value / 1000) * self.total_frames)
        self.show_frame(frame_number)

    def on_slider_released(self):
        """进度条释放后恢复播放状态"""
        if hasattr(self, 'was_playing') and self.was_playing:
            self.play()

    def update_slider(self):
        """更新进度条位置"""
        if self.total_frames > 0:
            progress = (self.current_frame / self.total_frames) * 1000
            self.slider.blockSignals(True)
            self.slider.setValue(int(progress))
            self.slider.blockSignals(False)

    def update_time_label(self):
        """更新时间显示"""
        current_time = self.get_current_time()
        self.time_label.setText(
            f"{self.format_time(current_time)} / {self.format_time(self.duration)}"
        )

    def get_current_time(self) -> float:
        """获取当前播放时间（秒）"""
        if self.fps > 0:
            return self.current_frame / self.fps
        return 0.0

    def seek_to_time(self, time_seconds: float):
        """跳转到指定时间（秒）"""
        if not self.cap:
            return

        frame_number = int(time_seconds * self.fps)
        frame_number = max(0, min(frame_number, self.total_frames - 1))
        self.show_frame(frame_number)

    @staticmethod
    def format_time(seconds: float) -> str:
        """格式化时间为 MM:SS.mmm"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds - int(seconds)) * 1000)
        return f"{minutes:02d}:{secs:02d}.{milliseconds:03d}"

    def closeEvent(self, event):
        """关闭时释放资源"""
        if self.cap:
            self.cap.release()
        event.accept()