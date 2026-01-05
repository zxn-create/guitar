import streamlit as st
import cv2
import pygame
import numpy as np
import time
import sys
import os
from typing import Dict, Any

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hand_tracker import HandTracker
from gesture_analyzer import GestureAnalyzer
from guitar_3d_engine import Guitar3DEngine
from audio_system import AudioSystem
import utils

class AirGuitarApp:
    """空气吉他主应用程序"""
    
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
                self.debug_info = f"识别成功: {current_chord} | 伸直手指: {extended_count}个 | 位置: {hand_position}"
        
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
    
    def render_chord_display(self, chord: str):
        """渲染和弦显示"""
        if chord and chord != "none" and chord != "unknown":
            chord_colors = {
                'C_major': '#FF6B6B',
                'G_major': '#4ECDC4', 
                'D_major': '#45B7D1',
                'A_minor': '#96CEB4',
                'E_minor': '#FFEAA7',
                'F_major': '#DDA0DD'
            }
            
            color = chord_colors.get(chord, '#FF6B6B')
            
            st.markdown(f"""
            <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, {color}, #2C3E50); 
                        border-radius: 15px; margin: 20px 0; box-shadow: 0 8px 25px rgba(0,0,0,0.3);">
                <h1 style="color: white; margin: 0; font-size: 3rem;">🎵 {chord}</h1>
                <p style="color: rgba(255,255,255,0.8); margin: 10px 0 0 0;">当前检测到的和弦</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #667eea, #764ba2); 
                        border-radius: 15px; margin: 20px 0;">
                <h2 style="color: white; margin: 0;">🎸 等待检测和弦...</h2>
                <p style="color: rgba(255,255,255,0.8); margin: 10px 0 0 0;">请做出和弦手势</p>
            </div>
            """, unsafe_allow_html=True)
    
    def render_chord_guide(self):
        """渲染和弦手势指南"""
        st.subheader("🎯 和弦手势指南 - 手指数量+位置")
        
        # 基于手指数量和位置的手势设计
        chords_guide = {
            'C_major': {
                'description': "✌️ 两指伸直 + 手部抬高",
                'instruction': "伸直任意两指，将手放在画面上半部分",
                'fingers': "2指伸直",
                'position': "较高位置（画面上半部）",
                'color': '#FF6B6B',
                'icon': '✌️'
            },
            'G_major': {
                'description': "✌️ 两指伸直 + 手部放低", 
                'instruction': "伸直任意两指，将手放在画面下半部分",
                'fingers': "2指伸直",
                'position': "较低位置（画面下半部）",
                'color': '#4ECDC4',
                'icon': '✌️'
            },
            'D_major': {
                'description': "🤟 三指伸直 + 手部抬高",
                'instruction': "伸直任意三指，将手放在画面上半部分",
                'fingers': "3指伸直",
                'position': "较高位置（画面上半部）",
                'color': '#45B7D1',
                'icon': '🤟'
            },
            'A_minor': {
                'description': "🤟 三指伸直 + 手部放低",
                'instruction': "伸直任意三指，将手放在画面下半部分",
                'fingers': "3指伸直",
                'position': "较低位置（画面下半部）",
                'color': '#96CEB4',
                'icon': '🤟'
            },
            'E_minor': {
                'description': "🖖 四指伸直 + 手部抬高",
                'instruction': "伸直任意四指，将手放在画面上半部分",
                'fingers': "4指伸直",
                'position': "较高位置（画面上半部）",
                'color': '#FFEAA7',
                'icon': '🖖'
            },
            'F_major': {
                'description': "🖖 四指伸直 + 手部放低",
                'instruction': "伸直任意四指，将手放在画面下半部分",
                'fingers': "4指伸直",
                'position': "较低位置（画面下半部）",
                'color': '#DDA0DD',
                'icon': '🖖'
            }
        }
        
        # 按列显示
        cols = st.columns(2)
        for i, (chord, info) in enumerate(chords_guide.items()):
            with cols[i % 2]:
                with st.container():
                    st.markdown(f"""
                    <div style="padding: 15px; background: {info['color']}20; border-radius: 10px; border-left: 4px solid {info['color']}; margin: 5px 0;">
                        <div style="display: flex; align-items: center; margin-bottom: 8px;">
                            <span style="font-size: 1.5em; margin-right: 10px;">{info['icon']}</span>
                            <h4 style="margin: 0; color: {info['color']};">{chord}</h4>
                        </div>
                        <p style="margin: 5px 0 0 0; font-size: 0.9em; font-weight: bold;">{info['description']}</p>
                        <p style="margin: 3px 0 0 0; font-size: 0.8em; color: #666;">{info['instruction']}</p>
                        <p style="margin: 2px 0 0 0; font-size: 0.8em; color: #888;">
                            🎯 {info['fingers']} | 📍 {info['position']}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
        
        # 位置示意图
        st.markdown("""
        <div style="background: #f8f9fa; padding: 15px; border-radius: 10px; margin: 10px 0;">
            <h4 style="margin: 0; color: #495057;">📍 位置示意图：</h4>
            <div style="text-align: center; margin: 10px 0;">
                <div style="background: #e74c3c; color: white; padding: 10px; margin: 5px; border-radius: 5px;">
                    🔺 较高位置 - 手在画面上半部（屏幕上半部分）
                </div>
                <div style="background: #f39c12; color: white; padding: 10px; margin: 5px; border-radius: 5px;">
                    🔸 中间位置 - 手在画面中部
                </div>
                <div style="background: #27ae60; color: white; padding: 10px; margin: 5px; border-radius: 5px;">
                    🔻 较低位置 - 手在画面下半部（屏幕下半部分）
                </div>
            </div>
            <p style="margin: 5px 0 0 0; font-size: 0.9em; color: #666;">
                💡 <strong>重要提示</strong>: 确保手指完全伸直，手部位置明显区分高低
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # 调试提示
        st.markdown("""
        <div style="background: #e3f2fd; padding: 15px; border-radius: 10px; margin: 10px 0;">
            <h4 style="margin: 0; color: #1976d2;">🔧 调试提示：</h4>
            <ul style="margin: 5px 0 0 0;">
                <li>查看下方<strong>识别信息</strong>了解当前检测状态</li>
                <li>确保手指<strong>完全伸直</strong>，不要半弯曲</li>
                <li>手部位置要<strong>明显区分高低</strong></li>
                <li>保持手势<strong>稳定1-2秒</strong>让系统识别</li>
                <li>查看控制台获取<strong>详细调试信息</strong></li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    def render_sidebar(self):
        """渲染侧边栏"""
        with st.sidebar:
            st.header("⚙️ 设置")
            
            # 音频设置
            volume = st.slider("音量", 0.0, 1.0, 0.7, key="volume")
            self.audio_system.set_volume(volume)
            
            # 识别设置
            st.header("🎯 识别设置")
            show_detailed_info = st.checkbox("显示详细识别信息", value=True)
            
            st.header("🎵 快速测试")
            
            # 和弦测试按钮
            test_cols = st.columns(3)
            with test_cols[0]:
                if st.button("C", width='stretch'):
                    self.audio_system.play_chord("C_major")
                    st.success("播放 C大调")
            with test_cols[1]:
                if st.button("G", width='stretch'):
                    self.audio_system.play_chord("G_major")
                    st.success("播放 G大调")
            with test_cols[2]:
                if st.button("D", width='stretch'):
                    self.audio_system.play_chord("D_major")
                    st.success("播放 D大调")
            
            test_cols2 = st.columns(3)
            with test_cols2[0]:
                if st.button("Am", width='stretch'):
                    self.audio_system.play_chord("A_minor")
                    st.success("播放 A小调")
            with test_cols2[1]:
                if st.button("Em", width='stretch'):
                    self.audio_system.play_chord("E_minor")
                    st.success("播放 E小调")
            with test_cols2[2]:
                if st.button("F", width='stretch'):
                    self.audio_system.play_chord("F_major")
                    st.success("播放 F大调")
            
            # 音频控制
            st.header("🔊 音频控制")
            audio_cols = st.columns(2)
            with audio_cols[0]:
                if st.button("测试单音", width='stretch'):
                    self.audio_system.play_note("A")
                    st.info("播放 A音")
            with audio_cols[1]:
                if st.button("停止所有", width='stretch'):
                    self.audio_system.stop_all()
                    st.info("停止所有音频")
            
            return {
                'volume': volume,
                'show_detailed_info': show_detailed_info
            }
    
    def run(self):
        """运行主应用程序"""
        st.title("🎸 Air Guitar Advanced - 智能空气吉他")
        
        # 渲染侧边栏
        settings = self.render_sidebar()
        
        # 初始化摄像头
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            st.error("❌ 无法访问摄像头，请检查摄像头连接")
            st.info("💡 请确保：")
            st.info("1. 摄像头已连接且未被其他程序占用")
            st.info("2. 浏览器已获得摄像头权限")
            st.info("3. 摄像头驱动程序正常")
            return
        
        st.success("✅ 摄像头初始化成功")
        
        # 创建占位符
        frame_placeholder = st.empty()
        status_placeholder = st.empty()
        chord_placeholder = st.empty()
        debug_placeholder = st.empty()
        
        # 控制按钮
        st.markdown("---")
        control_col1, control_col2, control_col3 = st.columns(3)
        with control_col1:
            stop_button = st.button("🛑 停止应用", key=self.get_unique_key("stop"), width='stretch', type="primary")
        with control_col2:
            test_all_button = st.button("🎵 测试所有和弦", key=self.get_unique_key("test_all"), width='stretch')
        with control_col3:
            if st.button("🔄 重新开始", key=self.get_unique_key("restart"), width='stretch'):
                st.rerun()
        
        # 显示和弦指南
        self.render_chord_guide()
        
        if test_all_button:
            # 测试所有和弦
            st.info("🎶 正在播放所有和弦...")
            for chord in ["C_major", "G_major", "D_major", "A_minor", "E_minor", "F_major"]:
                self.audio_system.play_chord(chord)
                time.sleep(0.8)
        
        self.is_running = True
        
        try:
            while self.is_running and cap.isOpened():
                if stop_button:
                    self.is_running = False
                    st.info("⏹️ 应用正在停止...")
                    break
                
                ret, frame = cap.read()
                if not ret:
                    st.error("❌ 无法读取摄像头帧")
                    break
                
                # 处理帧
                results = self.process_frame(frame)
                
                # 更新FPS
                self.update_fps()
                
                # 更新UI
                with frame_placeholder.container():
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.subheader("📷 实时视图")
                        if results['processed_frame'] is not None:
                            st.image(results['processed_frame'], channels="BGR", width='stretch')
                    
                    with col2:
                        st.subheader("👋 手部信息")
                        if results['hand_data']:
                            for i, hand in enumerate(results['hand_data']):
                                if hand['detected']:
                                    with st.container():
                                        st.write(f"**手 {i+1}**: {hand.get('hand_type', 'unknown')}")
                                        st.write(f"**和弦**: {hand.get('gesture', 'unknown')}")
                                        features = hand.get('hand_features', {})
                                        extended_count = features.get('extended_count', 0)
                                        extended_fingers = features.get('extended_fingers', [])
                                        st.write(f"**伸直手指**: {extended_count}个")
                                        
                                        # 显示手指状态
                                        finger_states = features.get('finger_states', {})
                                        if finger_states:
                                            st.write("**手指状态**:")
                                            finger_names = {
                                                'thumb': '大拇指',
                                                'index': '食指',
                                                'middle': '中指',
                                                'ring': '无名指',
                                                'pinky': '小指'
                                            }
                                            for finger, state in finger_states.items():
                                                status = "🟢 伸直" if state else "🔴 弯曲"
                                                display_name = finger_names.get(finger, finger)
                                                st.write(f"  {display_name}: {status}")
                        else:
                            st.warning("👋 未检测到手部，请将手放在摄像头前")
                            st.info("💡 提示：确保手部完全在画面内，光线充足")
                
                # 更新状态信息
                with status_placeholder.container():
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📊 FPS", f"{self.fps:.1f}")
                    with col2:
                        st.metric("👋 检测手部", len(results['hand_data']))
                    with col3:
                        if results['current_chord'] and results['current_chord'] != "none":
                            st.metric("🎵 当前和弦", results['current_chord'])
                        else:
                            st.metric("🎵 当前和弦", "等待中")
                
                # 更新和弦显示
                with chord_placeholder.container():
                    self.render_chord_display(results['current_chord'])
                
                # 更新调试信息
                with debug_placeholder.container():
                    if self.debug_info:
                        st.info(f"**识别信息**: {self.debug_info}")
                    elif results['hand_data'] and results['hand_data'][0]['detected']:
                        hand = results['hand_data'][0]
                        features = hand.get('hand_features', {})
                        extended_count = features.get('extended_count', 0)
                        extended_fingers = features.get('extended_fingers', [])
                        st.info(f"**检测状态**: 检测到手部，伸直{extended_count}个手指")
                    else:
                        st.info("**检测状态**: 等待手部检测...")
                
                # 添加小延迟以控制帧率
                time.sleep(0.03)
        
        except Exception as e:
            st.error(f"❌ 发生错误: {str(e)}")
            st.info("请检查控制台获取详细错误信息")
        
        finally:
            # 清理资源
            if cap.isOpened():
                cap.release()
                print("✅ 摄像头已释放")
            if hasattr(self, 'hand_tracker'):
                self.hand_tracker.release()
                print("✅ 手部追踪器已释放")
            if hasattr(self, 'audio_system'):
                self.audio_system.stop_all()
                print("✅ 音频系统已停止")
            
            st.success("✅ 应用已安全停止")
            st.info("🔄 如需重新启动，请刷新页面")

def main():
    """主函数"""
    try:
        app = AirGuitarApp()
        app.run()
    except Exception as e:
        st.error(f"❌ 应用启动失败: {str(e)}")
        st.info("""
        **可能的原因和解决方案：**
        1. **摄像头问题** - 检查摄像头连接和权限
        2. **依赖包缺失** - 运行 `pip install -r requirements.txt`
        3. **音频设备问题** - 检查系统音频设置
        4. **资源冲突** - 关闭其他可能占用摄像头的程序
        """)

if __name__ == "__main__":
    main()
