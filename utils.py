import numpy as np
import cv2
import yaml
import os
from typing import Dict, List, Tuple, Any

def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

def calculate_distance(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
    """计算两点之间的欧几里得距离"""
    return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

def normalize_coordinates(landmarks: List[Tuple[float, float]], image_shape: Tuple[int, int]) -> List[Tuple[float, float]]:
    """将坐标归一化到[0,1]范围"""
    height, width = image_shape
    normalized = []
    for x, y in landmarks:
        normalized.append((x / width, y / height))
    return normalized

def create_rotation_matrix(angle: float, axis: str = 'z') -> np.ndarray:
    """创建旋转矩阵"""
    cos_a = np.cos(angle)
    sin_a = np.sin(angle)
    
    if axis == 'x':
        return np.array([
            [1, 0, 0],
            [0, cos_a, -sin_a],
            [0, sin_a, cos_a]
        ])
    elif axis == 'y':
        return np.array([
            [cos_a, 0, sin_a],
            [0, 1, 0],
            [-sin_a, 0, cos_a]
        ])
    else:  # z轴
        return np.array([
            [cos_a, -sin_a, 0],
            [sin_a, cos_a, 0],
            [0, 0, 1]
        ])

def interpolate_color(color1: List[float], color2: List[float], factor: float) -> List[float]:
    """颜色插值"""
    return [
        color1[0] + (color2[0] - color1[0]) * factor,
        color1[1] + (color2[1] - color1[1]) * factor,
        color1[2] + (color2[2] - color1[2]) * factor
    ]

def ensure_directory(directory: str):
    """确保目录存在"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def load_audio_file(file_path: str) -> np.ndarray:
    """加载音频文件"""
    try:
        import librosa
        audio, _ = librosa.load(file_path, sr=44100, mono=False)
        return audio
    except Exception as e:
        print(f"Error loading audio file {file_path}: {e}")
        return np.zeros(44100)  # 1秒的静音

class FPSController:
    """FPS控制器"""
    def __init__(self, target_fps: int = 30):
        self.target_fps = target_fps
        self.frame_time = 1.0 / target_fps
        self.last_time = 0
        
    def wait(self, current_time: float) -> bool:
        """等待到下一帧时间"""
        elapsed = current_time - self.last_time
        if elapsed >= self.frame_time:
            self.last_time = current_time
            return True
        return False
