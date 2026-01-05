# main_app_enhanced.py
import streamlit as st
import cv2
import pygame
import numpy as np
import time
import sys
import os
import json
from typing import Dict, Any, List
from PIL import Image
import base64
from io import BytesIO

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hand_tracker import HandTracker
from gesture_analyzer import GestureAnalyzer
from guitar_3d_engine import Guitar3DEngine
from audio_system import AudioSystem
import utils

# 注入CSS样式
def inject_custom_css():
    st.markdown("""
    <style>
        /* 主背景和文本颜色 */
        .stApp {
            background: linear-gradient(135deg, #0f0c1d 0%, #1a1730 50%, #0f0c1d 100%);
            color: #ffffff;
        }
        
        /* 标题样式 */
        .main-header {
            background: linear-gradient(135deg, #6a11cb, #ff0080, #00d4ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-align: center;
            font-size: 3.5rem !important;
            font-weight: 800 !important;
            margin-bottom: 10px !important;
            text-shadow: 0 5px 15px rgba(106, 17, 203, 0.3);
        }
        
        .sub-header {
            color: #b8b5d0;
            text-align: center;
            font-size: 1.2rem;
            margin-bottom: 30px;
        }
        
        /* 侧边栏样式 */
        section[data-testid="stSidebar"] {
            background: linear-gradient(135deg, #1a1730, #151225) !important;
            border-right: 1px solid rgba(106, 17, 203, 0.3);
        }
        
        .stSidebar h1, .stSidebar h2, .stSidebar h3, .stSidebar h4, .stSidebar h5, .stSidebar h6 {
            color: #ffffff !important;
        }
        
        .stSidebar p, .stSidebar label, .stSidebar span {
            color: #b8b5d0 !important;
        }
        
        /* 滑块样式 */
        .stSlider > div > div > div {
            background: linear-gradient(90deg, #6a11cb, #00d4ff) !important;
        }
        
        .stSlider > div > div > div > div {
            background: #ffffff !important;
        }
        
        /* 选择框样式 */
        .stSelectbox > div > div > div {
            background: #1a1730 !important;
            border: 1px solid #6a11cb !important;
            color: #ffffff !important;
        }
        
        /* 按钮样式 */
        .stButton > button {
            background: linear-gradient(135deg, #6a11cb, #ff0080) !important;
            color: white !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 10px 20px !important;
            font-weight: bold !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 15px rgba(106, 17, 203, 0.3) !important;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(106, 17, 203, 0.5) !important;
            background: linear-gradient(135deg, #7a1bdb, #ff2090) !important;
        }
        
        .stButton > button:active {
            transform: translateY(1px) !important;
        }
        
        /* 主要按钮 - 停止/开始 */
        .primary-button > button {
            background: linear-gradient(135deg, #ff0080, #ff6b9d) !important;
        }
        
        /* 复选框样式 */
        .stCheckbox > label {
            color: #ffffff !important;
            font-weight: 500 !important;
        }
        
        .stCheckbox > div > div {
            background: #1a1730 !important;
            border: 2px solid #6a11cb !important;
        }
        
        /* 指标卡片样式 */
        [data-testid="stMetricValue"] {
            color: #00d4ff !important;
            font-size: 1.8rem !important;
            font-weight: bold !important;
        }
        
        [data-testid="stMetricLabel"] {
            color: #b8b5d0 !important;
        }
        
        /* 信息框样式 */
        .stAlert {
            background: rgba(106, 17, 203, 0.1) !important;
            border: 1px solid rgba(106, 17, 203, 0.3) !important;
            color: #ffffff !important;
            border-radius: 10px !important;
        }
        
        /* 成功消息 */
        .stSuccess {
            background: rgba(0, 212, 255, 0.1) !important;
            border: 1px solid rgba(0, 212, 255, 0.3) !important;
            color: #00d4ff !important;
        }
        
        /* 错误消息 */
        .stError {
            background: rgba(255, 0, 128, 0.1) !important;
            border: 1px solid rgba(255, 0, 128, 0.3) !important;
            color: #ff0080 !important;
        }
        
        /* 警告消息 */
        .stWarning {
            background: rgba(255, 200, 0, 0.1) !important;
            border: 1px solid rgba(255, 200, 0, 0.3) !important;
            color: #ffcc00 !important;
        }
        
        /* 信息消息 */
        .stInfo {
            background: rgba(106, 17, 203, 0.1) !important;
            border: 1px solid rgba(106, 17, 203, 0.3) !important;
            color: #b8b5d0 !important;
        }
        
        /* 分割线 */
        hr {
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent, #6a11cb, transparent);
            margin: 20px 0;
        }
        
        /* 卡片容器 */
        .custom-card {
            background: rgba(26, 23, 48, 0.8);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid rgba(106, 17, 203, 0.3);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
            margin-bottom: 20px;
        }
        
        /* 实时视图容器 */
        .video-container {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 15px;
            padding: 15px;
            border: 2px solid rgba(106, 17, 203, 0.3);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4);
        }
        
        /* 手部信息容器 */
        .hand-info-container {
            background: rgba(26, 23, 48, 0.9);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid rgba(0, 212, 255, 0.3);
            height: 100%;
        }
        
        /* 和弦显示容器 */
        .chord-display {
            background: linear-gradient(135deg, rgba(106, 17, 203, 0.3), rgba(0, 212, 255, 0.3));
            border-radius: 15px;
            padding: 25px;
            text-align: center;
            margin: 20px 0;
            border: 2px solid rgba(106, 17, 203, 0.5);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
        }
        
        /* 响应式调整 */
        @media (max-width: 768px) {
            .main-header {
                font-size: 2.2rem !important;
            }
            .video-container {
                padding: 10px;
            }
        }
    </style>
    """, unsafe_allow_html=True)

class ExplosionEffect:
    """爆炸特效管理器"""
    
    def __init__(self):
        self.effects = []
        self.last_effect_time = 0
        self.effect_duration = 1000  # 毫秒
        
    def trigger(self, position: tuple, color: str = "#FF6B6B"):
        """触发爆炸特效"""
        current_time = time.time() * 1000
        self.effects.append({
            'position': position,
            'color': color,
            'start_time': current_time,
            'particles': self._create_particles()
        })
    
    def _create_particles(self):
        """创建粒子效果"""
        particles = []
        for _ in range(20):
            angle = np.random.random() * 2 * np.pi
            speed = np.random.random() * 3 + 2
            size = np.random.randint(5, 15)
            particles.append({
                'angle': angle,
                'speed': speed,
                'size': size,
                'distance': 0
            })
        return particles
    
    def get_active_effects(self):
        """获取当前活跃的特效"""
        current_time = time.time() * 1000
        active_effects = []
        
        for effect in self.effects[:]:
            if current_time - effect['start_time'] < self.effect_duration:
                active_effects.append(effect)
            else:
                self.effects.remove(effect)
        
        return active_effects

class AirGuitarApp:
    """空气吉他主应用程序 - 增强版"""
    
    def __init__(self):
        self.config = utils.load_config()
        self.setup_components()
        
        # 状态变量
        self.is_running = False
        self.current_chord = "none"
        self.prev_hand_data = None
        self.frame_count = 0
        self.fps = 0
        self.last_fps_time = time.time()
        self.button_counter = 0
        self.chord_history = []
        self.debug_info = ""
        self.effect_manager = ExplosionEffect()
        self.last_chord_change = 0
        self.recognition_streak = 0
        self.success_count = 0
        
        # 和弦颜色映射
        self.chord_colors = {
            'C_major': {'primary': '#FF6B6B', 'secondary': '#FF8E8E', 'gradient': 'linear-gradient(135deg, #FF6B6B, #FF8E8E)'},
            'G_major': {'primary': '#4ECDC4', 'secondary': '#6ED9D1', 'gradient': 'linear-gradient(135deg, #4ECDC4, #6ED9D1)'},
            'D_major': {'primary': '#45B7D1', 'secondary': '#6BC9E0', 'gradient': 'linear-gradient(135deg, #45B7D1, #6BC9E0)'},
            'A_minor': {'primary': '#96CEB4', 'secondary': '#B0E0C9', 'gradient': 'linear-gradient(135deg, #96CEB4, #B0E0C9)'},
            'E_minor': {'primary': '#FFEAA7', 'secondary': '#FFF4D1', 'gradient': 'linear-gradient(135deg, #FFEAA7, #FFF4D1)'},
            'F_major': {'primary': '#DDA0DD', 'secondary': '#E8BBE8', 'gradient': 'linear-gradient(135deg, #DDA0DD, #E8BBE8)'},
            'none': {'primary': '#667eea', 'secondary': '#764ba2', 'gradient': 'linear-gradient(135deg, #667eea, #764ba2)'}
        }
    
    def setup_components(self):
        """设置各个组件"""
        try:
            self.hand_tracker = HandTracker(self.config['hand_tracking'])
            self.gesture_analyzer = GestureAnalyzer(self.config)
            self.audio_system = AudioSystem(self.config['audio'])
            self.guitar_3d = None
            print("✅ 所有组件初始化成功")
        except Exception as e:
            print(f"❌ 组件初始化失败: {e}")
            st.error(f"组件初始化失败: {e}")
    
    def get_unique_key(self, base_name: str) -> str:
        """生成唯一的元素key"""
        self.button_counter += 1
        return f"{base_name}_{self.button_counter}"
    
    def process_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """处理单帧图像"""
        # 手部追踪
        processed_frame, hand_data = self.hand_tracker.process_frame(frame)
        
        # 手势分析
        analyzed_data = []
        current_chord = "none"
        
        for hand in hand_data:
            analysis = self.gesture_analyzer.analyze_hand_position(hand, frame.shape)
            analyzed_data.append(analysis)
            
            if analysis['detected'] and analysis['gesture'] != "unknown":
                current_chord = analysis['gesture']
                # 更新调试信息
                features = analysis.get('hand_features', {})
                extended_count = features.get('extended_count', 0)
                hand_position = self.gesture_analyzer.get_hand_position(analysis['bounding_box'])
                confidence = analysis.get('confidence', 0)
                self.debug_info = f"🎯 {current_chord} | ✨ 置信度: {confidence:.1%} | 📍 {hand_position}"
                
                # 高置信度时触发特效
                if confidence > 0.8 and time.time() - self.last_chord_change > 0.5:
                    self.trigger_recognition_effect(current_chord)
                    self.last_chord_change = time.time()
                    self.success_count += 1
        
        # 更新和弦状态
        if current_chord != self.current_chord and current_chord != "unknown":
            self.on_chord_change(current_chord)
        
        # 检测扫弦动作
        if self.prev_hand_data and analyzed_data and len(analyzed_data) > 0:
            strum_direction = self.gesture_analyzer.calculate_strumming_direction(
                self.prev_hand_data[0], analyzed_data[0]
            )
            if strum_direction != "none":
                self.on_strum_detected(strum_direction)
        
        self.prev_hand_data = analyzed_data
        self.current_chord = current_chord
        
        return {
            'processed_frame': processed_frame,
            'hand_data': analyzed_data,
            'current_chord': current_chord
        }
    
    def trigger_recognition_effect(self, chord: str):
        """触发识别成功的特效"""
        # 触发爆炸特效
        self.effect_manager.trigger((50, 50), self.chord_colors[chord]['primary'])
        
        # 播放成功音效
        self.audio_system.play_effect("success", 0.2)
        
        # 视觉反馈
        print(f"✨ 手势识别成功: {chord}")
    
    def on_chord_change(self, new_chord: str):
        """处理和弦变化"""
        print(f"🎵 检测到和弦变化: {new_chord}")
        
        self.chord_history.append({
            'chord': new_chord,
            'time': time.time()
        })
        
        if len(self.chord_history) > 10:
            self.chord_history.pop(0)
        
        if new_chord != "none" and new_chord != "unknown":
            self.audio_system.play_chord(new_chord)
            self.recognition_streak += 1
    
    def on_strum_detected(self, direction: str):
        """处理扫弦检测"""
        print(f"🎸 检测到扫弦: {direction}")
        self.audio_system.play_effect("pick_noise", 0.3)
    
    def update_fps(self):
        """更新FPS计算"""
        self.frame_count += 1
        current_time = time.time()
        if current_time - self.last_fps_time >= 1.0:
            self.fps = self.frame_count / (current_time - self.last_fps_time)
            self.frame_count = 0
            self.last_fps_time = current_time
    
    def render_header(self):
        """渲染应用头部"""
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 30px 20px;
            border-radius: 15px;
            margin-bottom: 30px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            position: relative;
            overflow: hidden;
        ">
            <div style="position: absolute; top: -50px; right: -50px; width: 200px; height: 200px; 
                        background: rgba(255,255,255,0.1); border-radius: 50%;"></div>
            <div style="position: absolute; bottom: -80px; left: -80px; width: 250px; height: 250px; 
                        background: rgba(255,255,255,0.05); border-radius: 50%;"></div>
            
            <h1 style="color: white; font-size: 3.5rem; margin: 0; font-weight: 800; position: relative;">
                🎸 Air Guitar Pro
            </h1>
            <p style="color: rgba(255,255,255,0.9); font-size: 1.2rem; margin: 10px 0 0 0; position: relative;">
                智能手势识别空气吉他系统
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_stats_bar(self):
        """渲染状态统计栏"""
        cols = st.columns(4)
        
        with cols[0]:
            st.markdown(f"""
            <div style="
                background: white;
                padding: 15px;
                border-radius: 10px;
                text-align: center;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                border-left: 5px solid #667eea;
            ">
                <div style="font-size: 0.9rem; color: #666;">📊 帧率</div>
                <div style="font-size: 2rem; font-weight: bold; color: #333;">{self.fps:.1f}</div>
                <div style="font-size: 0.8rem; color: #888;">FPS</div>
            </div>
            """, unsafe_allow_html=True)
        
        with cols[1]:
            st.markdown(f"""
            <div style="
                background: white;
                padding: 15px;
                border-radius: 10px;
                text-align: center;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                border-left: 5px solid #4ECDC4;
            ">
                <div style="font-size: 0.9rem; color: #666;">🎯 识别次数</div>
                <div style="font-size: 2rem; font-weight: bold; color: #333;">{self.success_count}</div>
                <div style="font-size: 0.8rem; color: #888;">成功识别</div>
            </div>
            """, unsafe_allow_html=True)
        
        with cols[2]:
            streak_icon = "🔥" if self.recognition_streak > 3 else "✨"
            streak_color = "#FF6B6B" if self.recognition_streak > 3 else "#4ECDC4"
            st.markdown(f"""
            <div style="
                background: white;
                padding: 15px;
                border-radius: 10px;
                text-align: center;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                border-left: 5px solid {streak_color};
            ">
                <div style="font-size: 0.9rem; color: #666;">{streak_icon} 连续识别</div>
                <div style="font-size: 2rem; font-weight: bold; color: #333;">{self.recognition_streak}</div>
                <div style="font-size: 0.8rem; color: #888;">当前连击</div>
            </div>
            """, unsafe_allow_html=True)
        
        with cols[3]:
            current_time = time.strftime("%H:%M:%S")
            st.markdown(f"""
            <div style="
                background: white;
                padding: 15px;
                border-radius: 10px;
                text-align: center;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                border-left: 5px solid #FFEAA7;
            ">
                <div style="font-size: 0.9rem; color: #666;">🕒 运行时间</div>
                <div style="font-size: 1.8rem; font-weight: bold; color: #333;">{current_time}</div>
                <div style="font-size: 0.8rem; color: #888;">系统时间</div>
            </div>
            """, unsafe_allow_html=True)
    
    def render_chord_display(self, chord: str):
        """渲染和弦显示"""
        chord_info = self.chord_colors.get(chord, self.chord_colors['none'])
        
        # 获取活跃的特效
        active_effects = self.effect_manager.get_active_effects()
        
        # 创建特效HTML
        effects_html = ""
        for effect in active_effects:
            color = effect['color']
            effects_html += f"""
            <div class="explosion" style="
                position: absolute;
                top: {effect['position'][0]}%;
                left: {effect['position'][1]}%;
                width: 100px;
                height: 100px;
                pointer-events: none;
                z-index: 1000;
                animation: explode 1s ease-out;
            ">
                <div style="
                    position: absolute;
                    width: 100%;
                    height: 100%;
                    background: radial-gradient(circle, {color} 0%, transparent 70%);
                    animation: fadeOut 1s ease-out;
                "></div>
            </div>
            """
        
        st.markdown(f"""
        <style>
        @keyframes explode {{
            0% {{ transform: scale(0); opacity: 1; }}
            100% {{ transform: scale(3); opacity: 0; }}
        }}
        @keyframes fadeOut {{
            0% {{ opacity: 1; }}
            100% {{ opacity: 0; }}
        }}
        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.05); }}
        }}
        @keyframes float {{
            0%, 100% {{ transform: translateY(0px); }}
            50% {{ transform: translateY(-10px); }}
        }}
        .chord-display {{
            animation: pulse 2s infinite;
        }}
        </style>
        
        <div style="
            position: relative;
            text-align: center;
            padding: 50px 30px;
            background: {chord_info['gradient']};
            border-radius: 20px;
            margin: 30px 0;
            box-shadow: 0 15px 35px rgba(0,0,0,0.2);
            overflow: hidden;
            min-height: 200px;
        ">
            {effects_html}
            
            <div class="chord-display" style="position: relative; z-index: 2;">
                <h1 style="
                    color: white;
                    margin: 0;
                    font-size: 4rem;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                    animation: float 3s ease-in-out infinite;
                ">
                    {f"🎵 {chord}" if chord != "none" else "🎸 等待和弦"}
                </h1>
                
                <p style="
                    color: rgba(255,255,255,0.9);
                    margin: 15px 0 0 0;
                    font-size: 1.2rem;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
                ">
                    {f"完美识别！" if chord != "none" else "请做出和弦手势"}
                </p>
                
                <div style="
                    display: inline-block;
                    background: rgba(255,255,255,0.2);
                    padding: 8px 20px;
                    border-radius: 20px;
                    margin-top: 20px;
                    backdrop-filter: blur(10px);
                ">
                    <span style="color: white; font-size: 0.9rem;">
                        {f"🎯 实时识别中" if chord != "none" else "👋 等待手部检测"}
                    </span>
                </div>
            </div>
            
            <div style="
                position: absolute;
                bottom: 10px;
                right: 20px;
                color: rgba(255,255,255,0.6);
                font-size: 0.8rem;
            ">
                Air Guitar Pro v2.0
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def render_chord_guide(self):
        """渲染和弦手势指南"""
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 25px;
            border-radius: 15px;
            margin: 20px 0;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        ">
            <h3 style="color: #495057; margin: 0 0 20px 0;">
                🎯 和弦手势指南
            </h3>
        """, unsafe_allow_html=True)
        
        # 和弦指南卡片
        chords_guide = {
            'C_major': {'icon': '✌️', 'fingers': '2指', 'position': '高', 'desc': '两指伸直，手部抬高'},
            'G_major': {'icon': '✌️', 'fingers': '2指', 'position': '低', 'desc': '两指伸直，手部放低'},
            'D_major': {'icon': '🤟', 'fingers': '3指', 'position': '高', 'desc': '三指伸直，手部抬高'},
            'A_minor': {'icon': '🤟', 'fingers': '3指', 'position': '低', 'desc': '三指伸直，手部放低'},
            'E_minor': {'icon': '🖖', 'fingers': '4指', 'position': '高', 'desc': '四指伸直，手部抬高'},
            'F_major': {'icon': '🖖', 'fingers': '4指', 'position': '低', 'desc': '四指伸直，手部放低'}
        }
        
        # 每行显示3个和弦
        chords_list = list(chords_guide.items())
        for i in range(0, len(chords_list), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(chords_list):
                    chord, info = chords_list[i + j]
                    color_info = self.chord_colors[chord]
                    
                    with cols[j]:
                        st.markdown(f"""
                        <div style="
                            background: white;
                            padding: 20px;
                            border-radius: 12px;
                            margin: 10px 0;
                            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                            border-top: 5px solid {color_info['primary']};
                            transition: transform 0.3s;
                        ">
                            <div style="
                                display: flex;
                                align-items: center;
                                margin-bottom: 15px;
                            ">
                                <span style="font-size: 2rem; margin-right: 10px;">
                                    {info['icon']}
                                </span>
                                <div>
                                    <h4 style="margin: 0; color: {color_info['primary']};">
                                        {chord}
                                    </h4>
                                    <p style="margin: 5px 0 0 0; font-size: 0.9em; color: #666;">
                                        {info['desc']}
                                    </p>
                                </div>
                            </div>
                            
                            <div style="
                                display: flex;
                                justify-content: space-between;
                                margin-top: 10px;
                                padding-top: 10px;
                                border-top: 1px solid #eee;
                            ">
                                <div>
                                    <span style="font-size: 0.8em; color: #888;">手指</span>
                                    <div style="font-weight: bold; color: #333;">
                                        {info['fingers']}
                                    </div>
                                </div>
                                <div>
                                    <span style="font-size: 0.8em; color: #888;">位置</span>
                                    <div style="font-weight: bold; color: #333;">
                                        {info['position']}
                                    </div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # 位置示意图
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
            padding: 20px;
            border-radius: 12px;
            margin: 20px 0;
        ">
            <h4 style="color: #1976d2; margin: 0 0 15px 0;">📍 位置识别区域</h4>
            
            <div style="
                display: flex;
                justify-content: space-around;
                align-items: center;
                margin: 20px 0;
            ">
                <div style="text-align: center;">
                    <div style="
                        width: 80px;
                        height: 80px;
                        background: #e74c3c;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin: 0 auto 10px;
                        color: white;
                        font-size: 1.5rem;
                        box-shadow: 0 4px 8px rgba(231, 76, 60, 0.3);
                    ">
                        🔺
                    </div>
                    <div style="font-weight: bold; color: #333;">高位置</div>
                    <div style="font-size: 0.8em; color: #666;">画面上半部</div>
                </div>
                
                <div style="text-align: center;">
                    <div style="
                        width: 80px;
                        height: 80px;
                        background: #f39c12;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin: 0 auto 10px;
                        color: white;
                        font-size: 1.5rem;
                        box-shadow: 0 4px 8px rgba(243, 156, 18, 0.3);
                    ">
                        🔸
                    </div>
                    <div style="font-weight: bold; color: #333;">中位置</div>
                    <div style="font-size: 0.8em; color: #666;">画面中部</div>
                </div>
                
                <div style="text-align: center;">
                    <div style="
                        width: 80px;
                        height: 80px;
                        background: #27ae60;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin: 0 auto 10px;
                        color: white;
                        font-size: 1.5rem;
                        box-shadow: 0 4px 8px rgba(39, 174, 96, 0.3);
                    ">
                        🔻
                    </div>
                    <div style="font-weight: bold; color: #333;">低位置</div>
                    <div style="font-size: 0.8em; color: #666;">画面下半部</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def render_sidebar(self):
        """渲染侧边栏"""
        with st.sidebar:
            # 用户信息
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
                border-radius: 12px;
                margin-bottom: 20px;
                text-align: center;
            ">
                <div style="
                    width: 60px;
                    height: 60px;
                    background: white;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 auto 15px;
                    font-size: 1.5rem;
                ">
                    🎸
                </div>
                <h4 style="color: white; margin: 0;">音乐家</h4>
                <p style="color: rgba(255,255,255,0.8); margin: 5px 0 0 0; font-size: 0.9em;">
                    等级: 初级
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # 音频设置
            st.header("⚙️ 音频设置")
            
            volume = st.slider(
                "🔊 音量控制", 
                0.0, 1.0, 0.7, 
                0.1,
                format="%.1f",
                key=self.get_unique_key("volume")
            )
            self.audio_system.set_volume(volume)
            
            # 音效开关
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🎵 开启音效", key=self.get_unique_key("fx_on")):
                    st.success("音效已开启")
            with col2:
                if st.button("🔇 静音", key=self.get_unique_key("mute")):
                    self.audio_system.set_volume(0)
                    st.info("已静音")
            
            st.markdown("---")
            
            # 快速和弦测试
            st.header("🎵 和弦测试")
            
            test_chords = ["C_major", "G_major", "D_major", "A_minor", "E_minor", "F_major"]
            
            for chord in test_chords:
                col1, col2 = st.columns([3, 1])
                with col1:
                    color_info = self.chord_colors[chord]
                    st.markdown(f"""
                    <div style="
                        background: {color_info['primary']}15;
                        padding: 10px;
                        border-radius: 8px;
                        border-left: 3px solid {color_info['primary']};
                        margin: 5px 0;
                    ">
                        <span style="color: {color_info['primary']}; font-weight: bold;">
                            {chord}
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    if st.button("▶️", key=self.get_unique_key(f"test_{chord}")):
                        self.audio_system.play_chord(chord)
                        st.toast(f"播放 {chord}", icon="🎵")
            
            st.markdown("---")
            
            # 系统信息
            st.header("ℹ️ 系统信息")
            st.info("""
            **版本**: 2.0.0  
            **状态**: 运行中  
            **手势库**: 6个和弦  
            **识别模式**: 实时  
            """)
            
            return {'volume': volume}
    
    def render_recognition_debug(self, results: Dict[str, Any]):
        """渲染识别调试信息"""
        if results['hand_data']:
            hand = results['hand_data'][0]
            if hand['detected']:
                features = hand.get('hand_features', {})
                confidence = hand.get('confidence', 0)
                
                st.markdown("""
                <div style="
                    background: linear-gradient(135deg, #fdfcfb 0%, #e2d1c3 100%);
                    padding: 20px;
                    border-radius: 12px;
                    margin: 20px 0;
                ">
                    <h4 style="color: #333; margin: 0 0 15px 0;">🔍 识别详情</h4>
                """, unsafe_allow_html=True)
                
                # 置信度条
                confidence_color = "#27ae60" if confidence > 0.8 else "#f39c12" if confidence > 0.5 else "#e74c3c"
                st.markdown(f"""
                <div style="margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span style="font-size: 0.9em; color: #666;">识别置信度</span>
                        <span style="font-weight: bold; color: {confidence_color};">
                            {confidence:.1%}
                        </span>
                    </div>
                    <div style="
                        width: 100%;
                        height: 8px;
                        background: #eee;
                        border-radius: 4px;
                        overflow: hidden;
                    ">
                        <div style="
                            width: {confidence * 100}%;
                            height: 100%;
                            background: {confidence_color};
                            border-radius: 4px;
                        "></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # 手指状态
                if 'finger_states' in features:
                    cols = st.columns(5)
                    finger_names = ['大拇指', '食指', '中指', '无名指', '小指']
                    finger_keys = ['thumb', 'index', 'middle', 'ring', 'pinky']
                    
                    for idx, (col, finger_key, finger_name) in enumerate(zip(cols, finger_keys, finger_names)):
                        with col:
                            is_extended = features['finger_states'].get(finger_key, False)
                            icon = "🟢" if is_extended else "🔴"
                            status = "伸直" if is_extended else "弯曲"
                            
                            st.markdown(f"""
                            <div style="text-align: center;">
                                <div style="font-size: 1.5rem;">{icon}</div>
                                <div style="font-size: 0.8em; font-weight: bold; margin: 5px 0;">
                                    {finger_name}
                                </div>
                                <div style="font-size: 0.7em; color: { '#27ae60' if is_extended else '#e74c3c'}">
                                    {status}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
    
    def run(self):
        """运行主应用程序"""
        # 设置页面配置
        st.set_page_config(
            page_title="Air Guitar Pro",
            page_icon="🎸",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # 渲染头部
        self.render_header()
        
        # 渲染侧边栏
        settings = self.render_sidebar()
        
        # 初始化摄像头
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            st.error("""
            ❌ 无法访问摄像头
            """)
            
            st.markdown("""
            <div style="
                background: #fff3cd;
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
            ">
                <h4 style="color: #856404; margin: 0 0 10px 0;">🔧 故障排除指南</h4>
                <ol style="color: #856404; margin: 0; padding-left: 20px;">
                    <li>检查摄像头连接是否正常</li>
                    <li>确保浏览器已获得摄像头权限</li>
                    <li>关闭其他可能占用摄像头的程序</li>
                    <li>尝试刷新页面重新授权</li>
                    <li>检查摄像头驱动程序是否最新</li>
                </ol>
            </div>
            """, unsafe_allow_html=True)
            return
        
        st.success("✅ 摄像头初始化成功")
        
        # 创建占位符
        stats_placeholder = st.empty()
        chord_placeholder = st.empty()
        video_placeholder = st.empty()
        control_placeholder = st.empty()
        debug_placeholder = st.empty()
        
        # 控制按钮
        with control_placeholder.container():
            st.markdown("---")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("🎬 开始识别", key=self.get_unique_key("start"), 
                           type="primary", use_container_width=True):
                    self.is_running = True
                    st.toast("识别已启动", icon="🎸")
            
            with col2:
                if st.button("⏸️ 暂停识别", key=self.get_unique_key("pause"), 
                           use_container_width=True):
                    self.is_running = False
                    st.toast("识别已暂停", icon="⏸️")
            
            with col3:
                if st.button("🔄 重置统计", key=self.get_unique_key("reset"), 
                           use_container_width=True):
                    self.success_count = 0
                    self.recognition_streak = 0
                    st.toast("统计已重置", icon="🔄")
            
            with col4:
                if st.button("📹 拍照测试", key=self.get_unique_key("capture"), 
                           use_container_width=True):
                    if cap.isOpened():
                        ret, frame = cap.read()
                        if ret:
                            st.image(frame, channels="BGR", caption="摄像头测试")
                            st.toast("拍照成功", icon="📸")
        
        # 显示和弦指南
        self.render_chord_guide()
        
        # 主循环
        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    st.error("❌ 无法读取摄像头帧")
                    break
                
                # 处理帧
                results = self.process_frame(frame)
                
                # 更新FPS
                self.update_fps()
                
                # 更新状态栏
                with stats_placeholder.container():
                    self.render_stats_bar()
                
                # 更新和弦显示
                with chord_placeholder.container():
                    self.render_chord_display(results['current_chord'])
                
                # 更新视频显示
                with video_placeholder.container():
                    col1, col2 = st.columns([3, 2])
                    
                    with col1:
                        st.markdown("""
                        <div style="
                            background: white;
                            padding: 15px;
                            border-radius: 12px;
                            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                        ">
                            <h4 style="margin: 0 0 15px 0;">📷 实时识别画面</h4>
                        """, unsafe_allow_html=True)
                        
                        if results['processed_frame'] is not None:
                            st.image(results['processed_frame'], channels="BGR", use_column_width=True)
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown("""
                        <div style="
                            background: white;
                            padding: 15px;
                            border-radius: 12px;
                            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                            height: 100%;
                        ">
                            <h4 style="margin: 0 0 15px 0;">👋 手部状态</h4>
                        """, unsafe_allow_html=True)
                        
                        if results['hand_data']:
                            hand = results['hand_data'][0]
                            if hand['detected']:
                                gesture = hand.get('gesture', 'unknown')
                                confidence = hand.get('confidence', 0)
                                
                                st.markdown(f"""
                                <div style="
                                    background: {'#d4edda' if gesture != 'unknown' else '#fff3cd'};
                                    padding: 15px;
                                    border-radius: 8px;
                                    margin-bottom: 15px;
                                ">
                                    <div style="
                                        display: flex;
                                        align-items: center;
                                        margin-bottom: 10px;
                                    ">
                                        <span style="
                                            font-size: 1.5rem;
                                            margin-right: 10px;
                                        ">
                                            {'🎯' if gesture != 'unknown' else '👋'}
                                        </span>
                                        <div>
                                            <div style="font-weight: bold; font-size: 1.2rem;">
                                                {gesture if gesture != 'unknown' else '未识别'}
                                            </div>
                                            <div style="font-size: 0.9em; color: #666;">
                                                {hand.get('hand_type', 'unknown')}
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div style="
                                        display: flex;
                                        align-items: center;
                                        margin-top: 10px;
                                    ">
                                        <div style="flex-grow: 1;">
                                            <div style="
                                                width: 100%;
                                                height: 6px;
                                                background: #eee;
                                                border-radius: 3px;
                                                overflow: hidden;
                                            ">
                                                <div style="
                                                    width: {confidence * 100}%;
                                                    height: 100%;
                                                    background: {'#28a745' if confidence > 0.7 else '#ffc107'};
                                                    border-radius: 3px;
                                                "></div>
                                            </div>
                                        </div>
                                        <div style="
                                            margin-left: 10px;
                                            font-weight: bold;
                                            color: {'#28a745' if confidence > 0.7 else '#ffc107'};
                                        ">
                                            {confidence:.0%}
                                        </div>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.warning("👋 未检测到手部")
                        else:
                            st.info("👐 请将手放入摄像头视野")
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                
                # 更新调试信息
                with debug_placeholder.container():
                    self.render_recognition_debug(results)
                
                # 控制帧率
                time.sleep(0.03)
        
        except Exception as e:
            st.error(f"""
            ❌ 发生错误
            
            **错误信息**: {str(e)}
            """)
            
            st.markdown(f"""
            <div style="
                background: #f8d7da;
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
            ">
                <h4 style="color: #721c24; margin: 0 0 10px 0;">⚠️ 错误详情</h4>
                <pre style="
                    background: white;
                    padding: 15px;
                    border-radius: 5px;
                    overflow-x: auto;
                    color: #dc3545;
                ">{str(e)}</pre>
            </div>
            """, unsafe_allow_html=True)
        
        finally:
            # 清理资源
            if cap.isOpened():
                cap.release()
            
            st.success("""
            ✅ 应用已安全停止
            
            **所有资源已释放**
            """)

def main():
    """主函数"""
    try:
        # 添加自定义CSS
        st.markdown("""
        <style>
        /* 主标题动画 */
        @keyframes gradientBG {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        /* 卡片悬停效果 */
        .hover-card {
            transition: all 0.3s ease;
        }
        .hover-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.2) !important;
        }
        
        /* 按钮样式 */
        .stButton > button {
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            transform: scale(1.05);
        }
        
        /* 滚动条样式 */
        ::-webkit-scrollbar {
            width: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(135deg, #764ba2, #667eea);
        }
        </style>
        """, unsafe_allow_html=True)
        
        app = AirGuitarApp()
        app.run()
        
    except Exception as e:
        st.error(f"❌ 应用启动失败: {str(e)}")

if __name__ == "__main__":
    main()
