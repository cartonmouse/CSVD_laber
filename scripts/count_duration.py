#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频快速统计脚本
统计文件夹中MP4视频数量，按每个视频15秒计算总时长
"""

import os
import logging
import time
from pathlib import Path
from datetime import datetime, timedelta

# ========== 配置参数 ==========
ROOT_PATH = r"G:\huafeng_seg"
VIDEO_DURATION = 15  # 每个视频的时长（秒）
LOG_FILE = r"G:\huafeng_seg/video_stats.log"


# =============================


def setup_logging():
    """配置日志系统"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def format_duration(seconds):
    """
    将秒数格式化为易读的时间格式

    Args:
        seconds: 秒数
    Returns:
        str: 格式化的时间字符串
    """
    td = timedelta(seconds=int(seconds))
    hours = td.seconds // 3600
    minutes = (td.seconds % 3600) // 60
    secs = td.seconds % 60

    if td.days > 0:
        return f"{td.days}天 {hours}小时 {minutes}分钟 {secs}秒"
    elif hours > 0:
        return f"{hours}小时 {minutes}分钟 {secs}秒"
    elif minutes > 0:
        return f"{minutes}分钟 {secs}秒"
    else:
        return f"{secs}秒"


def scan_videos(root_path):
    """
    扫描文件夹中的所有MP4视频

    Args:
        root_path: 根文件夹路径
    Returns:
        tuple: (视频文件列表, 处理时间)
    """
    start_time = time.time()
    video_files = []

    root = Path(root_path)

    if not root.exists():
        logging.error(f"路径不存在: {root_path}")
        return video_files, 0

    logging.info(f"开始扫描文件夹: {root_path}")
    logging.info("=" * 60)

    # 递归查找所有.mp4文件
    mp4_files = list(root.rglob("*.mp4"))
    total_files = len(mp4_files)

    logging.info(f"找到 {total_files} 个MP4文件")

    # 记录每个视频文件信息
    for idx, video_file in enumerate(mp4_files, 1):
        video_files.append({
            'name': video_file.name,
            'relative_path': str(video_file.relative_to(root)),
            'duration': VIDEO_DURATION
        })

        # 每100个文件显示一次进度
        if idx % 100 == 0 or idx == total_files:
            elapsed = time.time() - start_time
            if idx > 0:
                avg_time = elapsed / idx
                remaining = avg_time * (total_files - idx)
                logging.info(f"进度: {idx}/{total_files} ({idx * 100 // total_files}%) - "
                             f"预计剩余: {format_duration(remaining)}")

    elapsed_time = time.time() - start_time
    logging.info(f"扫描完成，耗时: {elapsed_time:.2f}秒")

    return video_files, elapsed_time


def generate_report(root_path, video_files, scan_time):
    """
    生成统计报告

    Args:
        root_path: 根文件夹路径
        video_files: 视频文件列表
        scan_time: 扫描耗时
    """
    total_count = len(video_files)
    total_duration = total_count * VIDEO_DURATION

    logging.info("\n" + "=" * 60)
    logging.info("统计报告")
    logging.info("=" * 60)
    logging.info(f"扫描路径: {root_path}")
    logging.info(f"视频总数: {total_count} 个")
    logging.info(f"单个视频时长: {VIDEO_DURATION} 秒")
    logging.info(f"总时长: {format_duration(total_duration)} ({total_duration} 秒)")
    logging.info(f"扫描耗时: {scan_time:.2f} 秒")

    if total_count > 0:
        logging.info(f"平均时长: {VIDEO_DURATION} 秒/视频")

    # 标注时间估算
    logging.info("\n" + "-" * 60)
    logging.info("标注时间估算（假设标注速度为播放速度的3-5倍）:")
    logging.info(f"  乐观估计(3倍): {format_duration(total_duration * 3)}")
    logging.info(f"  中等估计(4倍): {format_duration(total_duration * 4)}")
    logging.info(f"  保守估计(5倍): {format_duration(total_duration * 5)}")
    logging.info("-" * 60)

    # 按一级子文件夹统计
    folder_stats = {}
    for video in video_files:
        parts = Path(video['relative_path']).parts
        # 只取第一级文件夹
        folder = parts[0] if len(parts) > 0 else 'root'
        if folder not in folder_stats:
            folder_stats[folder] = 0
        folder_stats[folder] += 1

    logging.info("\n各一级子文件夹统计:")
    logging.info("-" * 60)

    for folder, count in sorted(folder_stats.items()):
        duration = count * VIDEO_DURATION
        logging.info(f"{folder}：总视频时长：{format_duration(duration)}")

    logging.info("=" * 60)


def save_video_list(video_files):
    """
    保存详细视频列表到文件

    Args:
        video_files: 视频文件列表
    """
    output_file = "video_list.txt"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"详细视频列表 - 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")

        for idx, video in enumerate(video_files, 1):
            f.write(f"{idx}. {video['relative_path']}\n")
            f.write(f"   时长: {VIDEO_DURATION}秒\n\n")

    logging.info(f"详细视频列表已保存到: {output_file}")


def main():
    """主函数"""
    setup_logging()

    logging.info("视频快速统计工具")
    logging.info("=" * 60)

    overall_start = time.time()

    # 扫描视频
    video_files, scan_time = scan_videos(ROOT_PATH)

    # 生成报告
    if video_files:
        generate_report(ROOT_PATH, video_files, scan_time)
        save_video_list(video_files)
    else:
        logging.warning("未找到任何MP4视频文件")

    overall_time = time.time() - overall_start
    logging.info(f"\n总耗时: {overall_time:.2f}秒")


if __name__ == "__main__":
    main()