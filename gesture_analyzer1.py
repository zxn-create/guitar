import numpy as np
from typing import List, Dict, Tuple, Any
import utils

class GestureAnalyzer:
    """手势分析与和弦识别"""
    
    def __init__(self, config: Dict[str, Any] = None):
        if config is None:
            config = utils.load_config()
            
        self.guitar_config = config['guitar']
        self.chords_config = config['chords']
        
    def analyze_hand_position(self, hand_data: Dict, image_shape: Tuple[int, int]) -> Dict[str, Any]:
        """分析手部位置并映射到吉他指板"""
        if not hand_data:
            return {'detected': False}
            
        landmarks = hand_data['landmarks']
        finger_tips = self.get_finger_tips(landmarks)
        
        # 计算手部边界框
        x_coords = [lm[0] for lm in landmarks]
        y_coords = [lm[1] for lm in landmarks]
        
        hand_bbox = {
            'x_min': min(x_coords),
            'x_max': max(x_coords),
            'y_min': min(y_coords),
            'y_max': max(y_coords),
            'width': max(x_coords) - min(x_coords),
            'height': max(y_coords) - min(y_coords)
        }
        
        # 计算手部特征
        hand_features = self.calculate_hand_features(finger_tips, landmarks)
        
        # 识别和弦
        chord = self.recognize_chord_by_count_and_position(hand_features, hand_bbox)
        
        return {
            'detected': True,
            'hand_type': hand_data['type'],
            'finger_tips': finger_tips,
            'bounding_box': hand_bbox,
            'hand_features': hand_features,
            'gesture': chord
        }
    
    def get_finger_tips(self, landmarks: List[Tuple[float, float, float]]) -> Dict[str, Tuple[float, float]]:
        """获取手指尖端坐标"""
        return {
            'thumb': (landmarks[4][0], landmarks[4][1]),
            'index': (landmarks[8][0], landmarks[8][1]),
            'middle': (landmarks[12][0], landmarks[12][1]),
            'ring': (landmarks[16][0], landmarks[16][1]),
            'pinky': (landmarks[20][0], landmarks[20][1])
        }
    
    def calculate_hand_features(self, finger_tips: Dict, landmarks: List) -> Dict[str, Any]:
        """计算手部特征"""
        features = {}
        
        # 计算每个手指的伸直状态（排除拇指）
        finger_states = {}
        for finger in ['index', 'middle', 'ring', 'pinky']:
            finger_states[finger] = self.is_finger_extended_simple(finger, landmarks)
        
        features['finger_states'] = finger_states
        
        # 计算伸直手指数量（排除拇指）
        extended_count = sum(1 for state in finger_states.values() if state)
        features['extended_count'] = extended_count
        
        # 计算伸直手指的组合
        extended_fingers = [finger for finger, state in finger_states.items() if state]
        features['extended_fingers'] = extended_fingers
        
        # 调试信息
        print(f"手指状态: {finger_states}")
        print(f"伸直手指: {extended_fingers} (共{extended_count}个)")
        
        return features
    
    def is_finger_extended_simple(self, finger: str, landmarks: List) -> bool:
        """简化的手指伸直检测"""
        # 手指关键点索引
        finger_indices = {
            'index': [5, 6, 7, 8],
            'middle': [9, 10, 11, 12],
            'ring': [13, 14, 15, 16],
            'pinky': [17, 18, 19, 20]
        }
        
        if finger not in finger_indices:
            return False
        
        indices = finger_indices[finger]
        
        # 获取指尖和指根坐标
        tip = landmarks[indices[-1]]  # 指尖
        base = landmarks[indices[0]]  # 指根
        
        # 计算指尖到指根的距离
        distance = ((tip[0] - base[0])**2 + (tip[1] - base[1])**2) ** 0.5
        
        # 调整阈值 - 降低阈值以提高识别灵敏度
        return distance > 0.08  # 从0.1降低到0.08
    
    def recognize_chord_by_count_and_position(self, features: Dict, bbox: Dict) -> str:
        """基于手指数量和位置识别和弦"""
        extended_count = features['extended_count']
        hand_position = self.get_hand_position(bbox)
        
        print(f"调试信息: 伸直手指数={extended_count}, 位置={hand_position}")
        
        # 基于伸直手指数量和位置的识别
        # C大调：两指伸直，手部在较高位置
        if extended_count == 2 and hand_position == 'high':
            print("✅ 识别为 C大调: 两指伸直 + 手部抬高")
            return 'C_major'
        
        # G大调：两指伸直，手部在较低位置
        elif extended_count == 2 and hand_position == 'low':
            print("✅ 识别为 G大调: 两指伸直 + 手部放低")
            return 'G_major'
        
        # D大调：三指伸直，手部在较高位置
        elif extended_count == 3 and hand_position == 'high':
            print("✅ 识别为 D大调: 三指伸直 + 手部抬高")
            return 'D_major'
        
        # A小调：三指伸直，手部在较低位置
        elif extended_count == 3 and hand_position == 'low':
            print("✅ 识别为 A小调: 三指伸直 + 手部放低")
            return 'A_minor'
        
        # E小调：四指伸直，手部在较高位置
        elif extended_count == 4 and hand_position == 'high':
            print("✅ 识别为 E小调: 四指伸直 + 手部抬高")
            return 'E_minor'
        
        # F大调：四指伸直，手部在较低位置
        elif extended_count == 4 and hand_position == 'low':
            print("✅ 识别为 F大调: 四指伸直 + 手部放低")
            return 'F_major'
        
        print(f"❌ 未识别: 伸直{extended_count}指, 位置{hand_position}")
        return "unknown"
    
    def get_hand_position(self, bbox: Dict) -> str:
        """获取手部位置（高/中/低）"""
        vertical_center = (bbox['y_min'] + bbox['y_max']) / 2
        
        print(f"手部垂直位置: {vertical_center}")
        
        # 调整位置阈值，让"高"位置更容易识别
        if vertical_center < 0.5:  # 从0.4调整到0.5
            return 'high'
        elif vertical_center < 0.7:
            return 'middle'
        else:
            return 'low'
    
    def calculate_strumming_direction(self, prev_hand_data: Dict, current_hand_data: Dict) -> str:
        """计算扫弦方向"""
        if not prev_hand_data or not current_hand_data:
            return "none"
        
        if not prev_hand_data.get('detected', False) or not current_hand_data.get('detected', False):
            return "none"
            
        prev_y = prev_hand_data['bounding_box']['y_min']
        current_y = current_hand_data['bounding_box']['y_min']
        
        movement = current_y - prev_y
        
        if movement > 0.05:
            return "downstroke"
        elif movement < -0.05:
            return "upstroke"
        else:
            return "none"
