import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import bcrypt
import time

# 页面配置
st.set_page_config(
    page_title="融思政 - 数字图像处理实验平台",
    page_icon="🇨🇳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 数据库核心功能
def init_db():
    """初始化数据库，创建用户表和实验提交表"""
    conn = sqlite3.connect('image_processing_platform.db')
    c = conn.cursor()
    # 创建用户表（包含角色字段）
    c.execute(''' 
        CREATE TABLE IF NOT EXISTS users ( 
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            username TEXT UNIQUE NOT NULL, 
            password TEXT NOT NULL, 
            role TEXT NOT NULL, 
            create_time TEXT NOT NULL 
        ) 
    ''')
    
    # 创建实验提交表
    c.execute('''
        CREATE TABLE IF NOT EXISTS experiment_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_username TEXT NOT NULL,
            experiment_number INTEGER NOT NULL,
            experiment_title TEXT NOT NULL,
            submission_content TEXT NOT NULL,
            submission_time TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            teacher_feedback TEXT DEFAULT '',
            score INTEGER DEFAULT 0,
            resubmission_count INTEGER DEFAULT 0,
            allow_view_score BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (student_username) REFERENCES users (username)
        )
    ''')
    
    # 创建思政感悟表
    c.execute('''
        CREATE TABLE IF NOT EXISTS ideology_reflections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_username TEXT NOT NULL,
            reflection_content TEXT NOT NULL,
            submission_time TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            teacher_feedback TEXT DEFAULT '',
            score INTEGER DEFAULT 0,
            word_count INTEGER DEFAULT 0,
            allow_view_score BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (student_username) REFERENCES users (username)
        )
    ''')
    
    # 创建学习进度表
    c.execute('''
        CREATE TABLE IF NOT EXISTS learning_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            progress_type TEXT NOT NULL,
            progress_value REAL DEFAULT 0,
            update_time TEXT NOT NULL,
            FOREIGN KEY (username) REFERENCES users (username)
        )
    ''')
    
    conn.commit()
    conn.close()
    
    # 创建默认教师账号
    create_default_teachers()

def create_default_teachers():
    """创建默认的教师账号"""
    default_teachers = [
        {"username": "yhh", "password": "23123yhh", "role": "teacher"},
        {"username": "yhh1", "password": "23123yhh", "role": "teacher"},
        {"username": "yhh2", "password": "23123yhh", "role": "teacher"},
        {"username": "yhh3", "password": "23123yhh", "role": "teacher"},
        {"username": "yhh4", "password": "23123yhh", "role": "teacher"}
    ]
    
    conn = sqlite3.connect('image_processing_platform.db')
    c = conn.cursor()
    
    for teacher in default_teachers:
        try:
            # 检查用户是否已存在
            c.execute("SELECT id FROM users WHERE username = ?", (teacher["username"],))
            if c.fetchone() is None:
                # 密码哈希处理（加盐）
                salt = bcrypt.gensalt()
                hashed_password = bcrypt.hashpw(teacher["password"].encode('utf-8'), salt)
                create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                c.execute(
                    "INSERT INTO users (username, password, role, create_time) VALUES (?, ?, ?, ?)", 
                    (teacher["username"], hashed_password.decode('utf-8'), teacher["role"], create_time)
                )
                print(f"创建教师账号: {teacher['username']}")
        except Exception as e:
            print(f"创建教师账号 {teacher['username']} 失败: {str(e)}")
    
    conn.commit()
    conn.close()

def add_user(username, password, role):
    """添加新用户（密码哈希存储）"""
    try:
        conn = sqlite3.connect('image_processing_platform.db')
        c = conn.cursor()
        # 密码哈希处理（加盐）
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute(
            "INSERT INTO users (username, password, role, create_time) VALUES (?, ?, ?, ?)", 
            (username, hashed_password.decode('utf-8'), role, create_time)
        )
        conn.commit()
        conn.close()
        return True, "注册成功！"
    except sqlite3.IntegrityError:
        return False, "用户名已存在！"
    except Exception as e:
        return False, f"注册失败：{str(e)}"

def verify_user(username, password):
    """验证用户登录（匹配哈希密码）"""
    try:
        conn = sqlite3.connect('image_processing_platform.db')
        c = conn.cursor()
        c.execute("SELECT password, role FROM users WHERE username = ?", (username,))
        result = c.fetchone()
        conn.close()
        if result:
            hashed_password, role = result
            # 验证密码
            if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
                return True, role  # 登录成功，返回角色
        return False, None  # 用户名或密码错误
    except Exception as e:
        st.error(f"登录验证失败：{str(e)}")
        return False, None

def change_password(username, old_password, new_password):
    """修改用户密码"""
    try:
        # 首先验证旧密码
        success, role = verify_user(username, old_password)
        if not success:
            return False, "旧密码错误"
        
        # 更新为新密码
        conn = sqlite3.connect('image_processing_platform.db')
        c = conn.cursor()
        
        # 对新密码进行哈希处理
        salt = bcrypt.gensalt()
        hashed_new_password = bcrypt.hashpw(new_password.encode('utf-8'), salt)
        
        # 更新密码
        c.execute(
            "UPDATE users SET password = ? WHERE username = ?",
            (hashed_new_password.decode('utf-8'), username)
        )
        
        conn.commit()
        conn.close()
        return True, "密码修改成功！"
    except Exception as e:
        return False, f"修改密码失败：{str(e)}"

def get_user_stats():
    """获取用户统计数据"""
    try:
        conn = sqlite3.connect('image_processing_platform.db')
        c = conn.cursor()
        
        # 获取总用户数
        c.execute("SELECT COUNT(*) FROM users")
        total_users = c.fetchone()[0]
        
        # 获取学生数
        c.execute("SELECT COUNT(*) FROM users WHERE role = 'student'")
        student_count = c.fetchone()[0]
        
        # 获取实验提交总数
        c.execute("SELECT COUNT(*) FROM experiment_submissions")
        experiment_count = c.fetchone()[0]
        
        # 获取思政感悟总数
        c.execute("SELECT COUNT(*) FROM ideology_reflections")
        reflection_count = c.fetchone()[0]
        
        conn.close()
        
        return {
            'total_users': total_users,
            'student_count': student_count,
            'experiment_count': experiment_count,
            'reflection_count': reflection_count
        }
    except Exception as e:
        print(f"获取统计数据失败: {str(e)}")
        return {'total_users': 0, 'student_count': 0, 'experiment_count': 0, 'reflection_count': 0}

# 初始化数据库（首次运行自动创建）
init_db()

# 现代化米色思政主题CSS
def apply_modern_css():
    st.markdown("""
    <style>
    /* 现代化米色主题变量 */
    :root {
        --primary-red: #dc2626;
        --dark-red: #b91c1c;
        --accent-red: #ef4444;
        --light-red: #fee2e2;
        --beige-light: #fefaf0;
        --beige-medium: #fdf6e3;
        --beige-dark: #faf0d9;
        --gold: #d4af37;
        --light-gold: #fef3c7;
        --dark-text: #1f2937;
        --light-text: #6b7280;
        --card-shadow: 0 10px 25px -5px rgba(220, 38, 38, 0.1), 0 8px 10px -6px rgba(220, 38, 38, 0.1);
        --hover-shadow: 0 25px 50px -12px rgba(220, 38, 38, 0.25);
    }
    
    /* 整体页面背景 - 米色渐变 */
    .stApp {
        background: linear-gradient(135deg, #fefaf0 0%, #fdf6e3 50%, #faf0d9 100%);
    }
    
    /* 主容器 */
    .main-container {
        background: linear-gradient(135deg, #fefaf0 0%, #fdf6e3 50%, #faf0d9 100%);
        min-height: 100vh;
    }
    
    /* 现代化头部 */
    .modern-header {
        background: linear-gradient(135deg, var(--primary-red) 0%, var(--dark-red) 100%);
        color: white;
        padding: 40px;
        text-align: center;
        border-radius: 24px;
        margin: 20px 0 40px 0;
        box-shadow: var(--card-shadow);
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .modern-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 100" fill="%23ffffff" opacity="0.1"><polygon points="0,0 1000,50 1000,100 0,100"/></svg>');
        background-size: cover;
    }
    
    .main-title {
        font-size: 3rem;
        margin-bottom: 15px;
        font-weight: 800;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        position: relative;
        background: linear-gradient(135deg, #fff, #fef3c7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
    }
    
    .subtitle {
        font-size: 1.3rem;
        opacity: 0.95;
        line-height: 1.6;
        max-width: 800px;
        margin: 0 auto;
        font-weight: 300;
        position: relative;
        text-align: center;
    }
    
    /* 动态LOGO容器 */
    .logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 20px 0;
    }
    
    .dynamic-logo {
        width: 200px;
        height: 200px;
        animation: logoFloat 3s ease-in-out infinite;
    }
    
    @keyframes logoFloat {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }
    
    /* 现代化导航卡片 */
    .modern-nav-card {
        background: white;
        border-radius: 20px;
        padding: 40px 30px;
        box-shadow: var(--card-shadow);
        text-align: center;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
        border: 2px solid transparent;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        position: relative;
        overflow: hidden;
    }
    
    .modern-nav-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(220, 38, 38, 0.1), transparent);
        transition: left 0.6s;
    }
    
    .modern-nav-card:hover::before {
        left: 100%;
    }
    
    .modern-nav-card:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: var(--hover-shadow);
        border-color: var(--primary-red);
    }
    
    .modern-nav-card.lab {
        background: linear-gradient(135deg, #fff, var(--beige-light));
        border-top: 4px solid var(--primary-red);
    }
    
    .modern-nav-card.resources {
        background: linear-gradient(135deg, #fff, var(--beige-light));
        border-top: 4px solid var(--accent-red);
    }
    
    .modern-nav-card.footprint {
        background: linear-gradient(135deg, #fff, var(--beige-light));
        border-top: 4px solid var(--gold);
    }
    
    .modern-nav-card.achievement {
        background: linear-gradient(135deg, #fff, var(--beige-light));
        border-top: 4px solid var(--dark-red);
    }
    
    .modern-nav-card.submission {
        background: linear-gradient(135deg, #fff, var(--beige-light));
        border-top: 4px solid #10b981;
    }
    
    .nav-icon {
        font-size: 4.5rem;
        margin-bottom: 25px;
        filter: drop-shadow(2px 2px 4px rgba(0,0,0,0.1));
    }
    
    .modern-nav-card h3 {
        font-size: 1.8rem;
        margin-bottom: 15px;
        font-weight: 700;
        color: var(--dark-text);
    }
    
    .modern-nav-card p {
        color: var(--light-text);
        line-height: 1.6;
        font-size: 1.1rem;
        font-weight: 400;
    }
    
    /* 现代化思政资源区 */
    .modern-gallery {
        background: white;
        border-radius: 24px;
        padding: 50px 40px;
        box-shadow: var(--card-shadow);
        margin-top: 50px;
        border: 1px solid #e5e7eb;
    }
    
    .gallery-title {
        color: var(--primary-red);
        font-size: 2.4rem;
        margin-bottom: 40px;
        text-align: center;
        font-weight: 700;
        position: relative;
        padding-bottom: 20px;
    }
    
    .gallery-title::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 100px;
        height: 4px;
        background: linear-gradient(90deg, var(--primary-red), var(--gold));
        border-radius: 2px;
    }
    
    /* 现代化引用卡片 */
    .modern-quote {
        background: linear-gradient(135deg, var(--beige-light), #fff);
        padding: 40px;
        border-radius: 20px;
        border-left: 6px solid var(--primary-red);
        box-shadow: 0 8px 25px rgba(220, 38, 38, 0.1);
        margin-bottom: 40px;
        position: relative;
    }
    
    .modern-quote::before {
        content: '"';
        position: absolute;
        top: 20px;
        left: 30px;
        font-size: 4rem;
        color: var(--primary-red);
        opacity: 0.2;
        font-family: serif;
    }
    
    .quote-text {
        font-size: 1.5rem;
        font-style: italic;
        line-height: 1.8;
        margin-bottom: 25px;
        color: var(--dark-text);
        text-align: left;
        font-weight: 400;
        font-family: SimSun, serif;
    }
    
    .quote-author {
        text-align: left;
        color: var(--primary-red);
        font-weight: 600;
        font-size: 1.2rem;
        font-family: SimSun, serif;
    }
    
    /* 现代化科学家卡片网格 */
    .modern-scientists-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 30px;
        margin-top: 30px;
    }
    
    .modern-scientist-card {
        display: flex;
        align-items: center;
        gap: 25px;
        padding: 30px;
        background: linear-gradient(135deg, var(--beige-light), #fff);
        border-radius: 18px;
        transition: all 0.3s ease;
        border: 2px solid #e5e7eb;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
    }
    
    .modern-scientist-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px rgba(220, 38, 38, 0.15);
        border-color: var(--primary-red);
    }
    
    .modern-scientist-avatar {
        width: 90px;
        height: 90px;
        border-radius: 50%;
        background: linear-gradient(135deg, var(--primary-red), var(--dark-red));
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 2rem;
        font-weight: bold;
        box-shadow: 0 8px 20px rgba(220, 38, 38, 0.3);
        flex-shrink: 0;
        position: relative;
        overflow: hidden;
    }
    
    .modern-scientist-avatar::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, transparent, rgba(255,255,255,0.3), transparent);
        transform: rotate(45deg);
        transition: all 0.6s;
    }
    
    .modern-scientist-card:hover .modern-scientist-avatar::before {
        left: 100%;
    }
    
    .modern-scientist-info h4 {
        color: var(--primary-red);
        margin-bottom: 12px;
        font-size: 1.4rem;
        font-weight: 700;
        font-family: SimSun, serif;
    }
    
    .modern-scientist-desc {
        color: var(--light-text);
        font-size: 1rem;
        margin-bottom: 12px;
        font-weight: 500;
        font-family: SimSun, serif;
    }
    
    .modern-achievement-badge {
        background: linear-gradient(135deg, var(--primary-red), var(--accent-red));
        color: white;
        padding: 10px 20px;
        border-radius: 25px;
        font-size: 0.9rem;
        display: inline-block;
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    
    /* 现代化按钮 - 红白渐变悬浮效果 */
    .stButton button {
        background: linear-gradient(135deg, #ffffff, #fef2f2);
        color: #dc2626;
        border: 2px solid #dc2626;
        padding: 14px 28px;
        border-radius: 50px;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(220, 38, 38, 0.2);
        transition: all 0.3s ease;
        font-size: 1rem;
        letter-spacing: 0.5px;
        position: relative;
        overflow: hidden;
    }
    
    .stButton button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(220, 38, 38, 0.1), transparent);
        transition: left 0.6s;
    }
    
    .stButton button:hover {
        background: linear-gradient(135deg, #dc2626, #b91c1c);
        color: white;
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(220, 38, 38, 0.4);
        border-color: #dc2626;
    }
    
    .stButton button:hover::before {
        left: 100%;
    }
    
    /* 特殊按钮样式 - 金色边框 */
    .stButton button.gold-btn {
        border: 2px solid #d4af37;
        color: #d4af37;
        background: linear-gradient(135deg, #fffdf6, #fefaf0);
    }
    
    .stButton button.gold-btn:hover {
        background: linear-gradient(135deg, #d4af37, #b8941f);
        color: white;
        border-color: #d4af37;
    }
    
    /* 整体页面内容区域 */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        background: linear-gradient(135deg, #fefaf0 0%, #fdf6e3 50%, #faf0d9 100%);
    }
    
    /* 侧边栏样式 - 米色渐变 */
    section[data-testid="stSidebar"] {
        background: linear-gradient(135deg, #fdf6e3 0%, #faf0d9 50%, #f5e6c8 100%) !important;
    }
    
    .css-1d391kg {
        background: linear-gradient(135deg, #fdf6e3 0%, #faf0d9 50%, #f5e6c8 100%) !important;
    }
    
    /* 侧边栏内容容器 */
    .css-1lcbmhc {
        background: transparent !important;
    }
    
    /* 响应式设计 */
    @media (max-width: 768px) {
        .modern-scientists-grid {
            grid-template-columns: 1fr;
        }
        .main-title {
            font-size: 2.2rem;
        }
        .subtitle {
            font-size: 1.1rem;
        }
        .modern-nav-card {
            padding: 30px 20px;
        }
        .dynamic-logo {
            width: 150px;
            height: 150px;
        }
    }
    
    /* 右上角用户区域样式 */
    .user-area {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1000;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .user-info {
        display: flex;
        align-items: center;
        gap: 10px;
        background: linear-gradient(135deg, #ffffff, #fef2f2);
        padding: 8px 16px;
        border-radius: 50px;
        border: 2px solid #dc2626;
        box-shadow: 0 4px 15px rgba(220, 38, 38, 0.2);
    }
    
    .user-avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: linear-gradient(135deg, #dc2626, #b91c1c);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: 0.9rem;
    }
    
    /* 登录注册对话框样式 */
    .login-dialog {
        background: white;
        padding: 30px;
        border-radius: 20px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        border: 2px solid #dc2626;
        margin: 20px 0;
    }
    
    /* 修改密码对话框样式 */
    .change-password-dialog {
        background: white;
        padding: 30px;
        border-radius: 20px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        border: 2px solid #10b981;
        margin: 20px 0;
    }
    
    /* 角色选择样式 */
    .role-selection {
        display: flex;
        gap: 10px;
        margin-bottom: 20px;
    }
    
    .role-btn {
        flex: 1;
        padding: 15px;
        border: 2px solid #dc2626;
        border-radius: 10px;
        background: white;
        color: #dc2626;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .role-btn.active {
        background: #dc2626;
        color: white;
    }
    
    .role-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(220, 38, 38, 0.3);
    }
    
    /* 教师账号提示样式 */
    .teacher-accounts-info {
        background: linear-gradient(135deg, #fef3c7, #fde68a);
        padding: 15px;
        border-radius: 10px;
        border: 2px solid #d4af37;
        margin: 15px 0;
    }
    </style>
    """, unsafe_allow_html=True)

def create_activity_chart():
    """创建学习活动图表"""
    days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    activity = [4, 3, 5, 6, 4, 7, 5]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=days,
        y=activity,
        mode='lines+markers',
        name='学习活跃度',
        line=dict(color='#dc2626', width=4),
        marker=dict(size=8, color='#dc2626')
    ))
    
    fig.update_layout(
        title="本周学习活跃度",
        xaxis_title="日期",
        yaxis_title="活跃度",
        template="plotly_white",
        height=300,
        font=dict(family="Arial, sans-serif")
    )
    
    return fig

def create_dynamic_logo():
    """创建动态思政LOGO - 使用HTML组件确保动画运行"""
    logo_html = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <title>思政主题红金动态LOGO</title>
        <style>
            body {
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                background: transparent;
                margin: 0;
                padding: 0;
            }
            .logo-container {
                width: 200px;
                height: 200px;
                position: relative;
                animation: float 3s ease-in-out infinite;
            }
            @keyframes float {
                0%, 100% { transform: translateY(0px); }
                50% { transform: translateY(-10px); }
            }
        </style>
    </head>
    <body>
        <svg class="logo-container" viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg">
            <!-- 外圈：红金渐变+动态光晕 -->
            <circle cx="200" cy="200" r="180" fill="none" 
                    stroke="url(#ring-gradient)" stroke-width="15" />
            <defs>
                <linearGradient id="ring-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#e50000" />
                    <stop offset="100%" stop-color="#d4af37" />
                </linearGradient>
                
                <linearGradient id="dot-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#d4af37" />
                    <stop offset="100%" stop-color="#e50000" />
                </linearGradient>

                <!-- 光晕滤镜 -->
                <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="3" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
            </defs>

            <!-- 核心元素：红金主体+呼吸动画 -->
            <g id="ideology-core" filter="url(#glow)">
                <!-- 红色主形（思政底色） -->
                <path d="M150,210 L250,210 L250,290 L200,290 L200,330 L150,330 Z" 
                      fill="#e50000" />
                <!-- 金色党徽元素（强化标识） -->
                <path d="M180,190 L200,170 L220,190 L200,210 Z" 
                      fill="#d4af37" stroke="#e50000" stroke-width="2" />
                <path d="M200,170 C215,160 230,180 230,200" 
                      stroke="#d4af37" stroke-width="4" fill="none" />
            </g>

            <!-- 引领线：金色+旋转+端点闪烁 -->
            <g id="guide-lines">
                <line x1="200" y1="200" x2="200" y2="110" 
                      stroke="#d4af37" stroke-width="4" stroke-linecap="round" />
                <line x1="200" y1="200" x2="290" y2="290" 
                      stroke="#d4af37" stroke-width="4" stroke-linecap="round" />
                <line x1="200" y1="200" x2="110" y2="290" 
                      stroke="#d4af37" stroke-width="4" stroke-linecap="round" />
                <!-- 端点（红金渐变+闪烁） -->
                <circle class="dot" cx="200" cy="110" r="10" 
                        fill="url(#dot-gradient)" stroke="#d4af37" stroke-width="2" />
                <circle class="dot" cx="290" cy="290" r="10" 
                        fill="url(#dot-gradient)" stroke="#d4af37" stroke-width="2" />
                <circle class="dot" cx="110" cy="290" r="10" 
                        fill="url(#dot-gradient)" stroke="#d4af37" stroke-width="2" />
            </g>
        </svg>

        <script>
            const guideLines = document.getElementById('guide-lines');
            const core = document.getElementById('ideology-core');
            const dots = document.querySelectorAll('.dot');
            let deg = 0;
            let scale = 1;
            let scaleDir = 0.002;
            let dotOpacity = 1;
            let dotDir = -0.01;

            // 多动画同步
            function animate() {
                // 引领线旋转
                deg += 0.08;
                guideLines.setAttribute('transform', `rotate(${deg} 200 200)`);

                // 核心元素呼吸
                scale += scaleDir;
                if (scale >= 1.05 || scale <= 0.95) scaleDir *= -1;
                core.setAttribute('transform', `scale(${scale})`);

                // 端点闪烁
                dotOpacity += dotDir;
                if (dotOpacity >= 1 || dotOpacity <= 0.6) dotDir *= -1;
                dots.forEach(dot => dot.setAttribute('opacity', dotOpacity));

                requestAnimationFrame(animate);
            }
            animate();
        </script>
    </body>
    </html>
    """
    
    # 使用components.v1.html来嵌入完整的HTML文件
    st.components.v1.html(logo_html, height=250)

def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        create_dynamic_logo()
        st.markdown("""
        <div style='background: linear-gradient(135deg, #dc2626, #b91c1c); color: white; 
            padding: 25px; border-radius: 15px; text-align: center; margin-bottom: 25px;
            box-shadow: 0 6px 12px rgba(220, 38, 38, 0.3);'>
            <h3 style='margin: 0;'>🇨🇳 思政引领</h3>
            <p style='margin: 10px 0 0 0; font-size: 1rem;'>科技报国 · 创新发展</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 快速导航
        st.markdown("### 🧭 快速导航")
        
        # 修复导航按钮 - 使用正确的页面路径
        if st.button("🏠 返回首页", use_container_width=True):
            st.switch_page("main.py")
        if st.button("🔬 图像处理实验室", use_container_width=True):
            st.switch_page("pages/1_🔬_图像处理实验室.py")
        if st.button("📝 智能与传统图片处理", use_container_width=True):
            # 使用JavaScript在新标签页打开链接
            st.switch_page("pages/智能与传统图片处理.py")
        if st.button("🏫加入班级与在线签到", use_container_width=True):
            st.switch_page("pages/分班和在线签到.py")
        if st.button("📤 实验作业提交", use_container_width=True):
            st.switch_page("pages/实验作业提交.py")
        if st.button("📚 学习资源中心", use_container_width=True):
            st.switch_page("pages/2_📚_学习资源中心.py")
        if st.button("📝 我的思政足迹", use_container_width=True):
            st.switch_page("pages/3_📝_我的思政足迹.py")

        if st.button("🏆 成果展示", use_container_width=True):
            st.switch_page("pages/4_🏆_成果展示.py")
        
        # 平台特色
        st.markdown("""
        <div style='background: linear-gradient(135deg, #fee2e2, #fecaca); padding: 25px; 
                    border-radius: 15px; border-left: 5px solid #dc2626; margin-bottom: 20px;
                    box-shadow: 0 4px 15px rgba(220, 38, 38, 0.2);'>
            <h4 style='color: #dc2626;'>🎯 平台特色</h4>
            <ul style='padding-left: 20px; color: #7f1d1d;'>
                <li style='color: #dc2626;'>🔬 专业图像处理</li>
                <li style='color: #dc2626;'>🇨🇳 思政教育融合</li>
                <li style='color: #dc2626;'>💡 创新实践平台</li>
                <li style='color: #dc2626;'>🚀 现代化技术栈</li>
                <li style='color: #dc2626;'>📤 作业提交系统</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # 思政教育目标
        st.markdown("""
        <div style='background: linear-gradient(135deg, #fee2e2, #fecaca); padding: 20px; 
                    border-radius: 12px; border: 2px solid #dc2626; margin-bottom: 20px;
                    box-shadow: 0 4px 15px rgba(220, 38, 38, 0.2);'>
            <h5 style='color: #dc2626;'>💡 思政教育目标</h5>
            <p style='font-size: 0.9rem; color: #7f1d1d;'>培养具有：</p>
            <ul style='padding-left: 15px; font-size: 0.85rem; color: #7f1d1d;'>
                <li style='color: #dc2626;'>🎯 工匠精神</li>
                <li style='color: #dc2626;'>🔬 科学态度</li>
                <li style='color: #dc2626;'>💡 创新意识</li>
                <li style='color: #dc2626;'>🇨🇳 家国情怀</li>
                <li style='color: #dc2626;'>📚 自主学习能力</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # 新增：今日思政金句
        st.markdown("""
        <div style='background: linear-gradient(135deg, #fef3c7, #fde68a); padding: 20px; 
                    border-radius: 12px; border: 2px solid #d4af37; margin-bottom: 20px;
                    box-shadow: 0 4px 15px rgba(212, 175, 55, 0.2);'>
            <h5 style='color: #b45309; text-align: center;'>💫 今日思政金句</h5>
            <p style='font-size: 0.9rem; color: #78350f; text-align: center; font-style: italic;'>
            "科技是国家强盛之基，创新是民族进步之魂。"
            </p>
            <p style='font-size: 0.8rem; color: #92400e; text-align: right; margin-top: 10px;'>
            —— 习近平
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # 系统信息
        st.markdown("---")
        st.markdown("**📊 系统信息**")
        st.text(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        st.text("状态: 🟢 正常运行")
        st.text("版本: v2.1.0")
        
        # 新增：用户进度
        st.markdown("---")
        st.markdown("**📈 学习进度**")
        progress = st.progress(65)
        st.caption("已完成 65% 的课程内容")

def render_user_area():
    """渲染右上角用户区域"""
    # 使用HTML定位右上角区域
    st.markdown("""
    <div class="user-area">
    """, unsafe_allow_html=True)
    
    # 使用列布局在右上角创建用户区域
    col1, col2, col3 = st.columns([6, 2, 2])
    
    with col3:
        if st.session_state.logged_in:
            # 已登录状态 - 显示用户信息和功能按钮
            username = st.session_state.username
            role = st.session_state.role
            avatar_text = username[0].upper() if username else "U"
            
            # 用户信息显示
            col_user1, col_user2 = st.columns([1, 3])
            with col_user1:
                st.markdown(f"""
                <div style='
                    width: 45px;
                    height: 45px;
                    border-radius: 50%;
                    background: linear-gradient(135deg, #dc2626, #b91c1c);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: bold;
                    font-size: 1.2rem;
                    box-shadow: 0 4px 12px rgba(220, 38, 38, 0.4);
                    border: 2px solid white;
                    position: relative;
                    overflow: hidden;
                '>
                    {avatar_text}
                    <div style='
                        position: absolute;
                        top: -50%;
                        left: -50%;
                        width: 200%;
                        height: 200%;
                        background: linear-gradient(45deg, transparent, rgba(255,255,255,0.3), transparent);
                        transform: rotate(45deg);
                    '></div>
                </div>
                """, unsafe_allow_html=True)
            with col_user2:
                st.markdown(f"""
                <div style='text-align: left; padding: 5px 0;'>
                    <div style='font-weight: bold; color: #dc2626; font-size: 1rem; margin-bottom: 2px; line-height: 1.2;'>{username}</div>
                    <div style='color: #6b7280; font-size: 0.75rem; line-height: 1.2;'>{role}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # 功能按钮区域
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                # 修改密码按钮
                if st.button("🔑 改密", 
                           key="change_pwd_btn", 
                           help="修改密码", 
                           use_container_width=True,
                           type="secondary"):
                    st.session_state.show_change_password = True
                    st.rerun()
            with col_btn2:
                # 退出登录按钮
                if st.button("🚪 退出", 
                           key="logout_btn", 
                           help="退出登录", 
                           use_container_width=True,
                           type="secondary"):
                    st.session_state.logged_in = False
                    st.session_state.username = ""
                    st.session_state.role = ""
                    st.session_state.show_login = False
                    st.session_state.show_change_password = False
                    st.rerun()
                
        else:
            # 未登录状态 - 显示登录/注册按钮
            if st.button("👤 登录/注册", 
                        key="login_btn", 
                        help="登录/注册", 
                        use_container_width=True,
                        type="primary"):
                st.session_state.show_login = True
                st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

def render_change_password_dialog():
    """渲染修改密码对话框"""
    if st.session_state.get('show_change_password', False):
        # 使用容器创建对话框效果
        with st.container():
            st.markdown("""
            <div class='change-password-dialog'>
            """, unsafe_allow_html=True)
            
            st.markdown("### 🔑 修改密码")
            st.info("为了保护您的账户安全，请定期修改密码。")
            
            with st.form("change_password_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    old_password = st.text_input("🔒 当前密码", 
                                                type="password", 
                                                placeholder="请输入当前密码",
                                                key="old_password")
                
                with col2:
                    new_password = st.text_input("🔐 新密码", 
                                                type="password", 
                                                placeholder="请输入新密码",
                                                key="new_password",
                                                help="建议使用8位以上包含字母、数字和特殊字符的组合")
                
                confirm_password = st.text_input("✅ 确认新密码", 
                                                type="password", 
                                                placeholder="请再次输入新密码",
                                                key="confirm_password")
                
                col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
                
                with col_btn1:
                    submit_btn = st.form_submit_button("💾 确认修改", 
                                                      use_container_width=True,
                                                      type="primary")
                with col_btn2:
                    if st.form_submit_button("❌ 取消", 
                                           use_container_width=True,
                                           type="secondary"):
                        st.session_state.show_change_password = False
                        st.rerun()
                
                if submit_btn:
                    if not old_password or not new_password or not confirm_password:
                        st.error("⚠️ 请填写所有密码字段")
                    elif new_password != confirm_password:
                        st.error("❌ 两次输入的新密码不一致")
                    elif len(new_password) < 6:
                        st.error("❌ 新密码长度至少6位")
                    elif old_password == new_password:
                        st.error("❌ 新密码不能与旧密码相同")
                    else:
                        # 调用修改密码函数
                        success, message = change_password(
                            st.session_state.username, 
                            old_password, 
                            new_password
                        )
                        
                        if success:
                            st.success(f"✅ {message}")
                            st.balloons()
                            # 等待2秒后关闭对话框
                            time.sleep(2)
                            st.session_state.show_change_password = False
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
            
            st.markdown("</div>", unsafe_allow_html=True)

def render_login_dialog():
    """渲染登录注册对话框"""
    if st.session_state.get('show_login', False):
        # 使用容器创建对话框效果
        with st.container():
            
            # 标题
            st.markdown("### 👤 用户登录/注册")
            
            # 角色选择
            st.markdown("#### 请选择您的身份")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🎓 学生端", key="student_role", use_container_width=True):
                    st.session_state.selected_role = "student"
            with col2:
                if st.button("👨‍🏫 教师端", key="teacher_role", use_container_width=True):
                    st.session_state.selected_role = "teacher"
            
            # 显示当前选择的角色
            if 'selected_role' in st.session_state:
                role_display = "🎓 学生" if st.session_state.selected_role == "student" else "👨‍🏫 教师"
                st.info(f"当前选择身份：{role_display}")
            
            # 使用选项卡
            login_tab, register_tab = st.tabs(["🔐 登录", "📝 注册"])
            
            with login_tab:
                with st.form("login_form_modal", clear_on_submit=True):
                    st.markdown("#### 登录账号")
                    login_username = st.text_input("👤 用户名", placeholder="请输入用户名", key="login_username_modal")
                    login_password = st.text_input("🔒 密码", type="password", placeholder="请输入密码", key="login_password_modal")
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        login_submitted = st.form_submit_button("🚀 立即登录", use_container_width=True)
                    with col_btn2:
                        if st.form_submit_button("❌ 取消", use_container_width=True):
                            st.session_state.show_login = False
                            st.rerun()
                    
                    if login_submitted:
                        if login_username and login_password:
                            success, role = verify_user(login_username, login_password)
                            if success:
                                st.session_state.logged_in = True
                                st.session_state.username = login_username
                                st.session_state.role = role
                                st.session_state.show_login = False
                                st.success("🎉 登录成功！")
                                st.rerun()
                            else:
                                st.error("❌ 用户名或密码错误")
                        else:
                            st.warning("⚠️ 请输入用户名和密码")
            
            with register_tab:
                with st.form("register_form_modal", clear_on_submit=True):
                    st.markdown("#### 注册新账号")
                    register_username = st.text_input("👤 用户名", placeholder="请输入用户名", key="register_username_modal")
                    register_password = st.text_input("🔒 密码", type="password", placeholder="请输入密码", key="register_password_modal")
                    confirm_password = st.text_input("✅ 确认密码", type="password", placeholder="请再次输入密码", key="confirm_password_modal")
                    
                    # 角色选择 - 教师端只能登录，注册时只能选择学生
                    role_options = {
                        "student": "🎓 学生"
                    }
                    selected_role = st.selectbox(
                        "选择身份",
                        options=list(role_options.keys()),
                        format_func=lambda x: role_options[x],
                        key="register_role"
                    )
                    
                    st.info("💡 教师账号已预置，如需教师权限请联系管理员")
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        register_submitted = st.form_submit_button("🚀 立即注册", use_container_width=True)
                    with col_btn2:
                        if st.form_submit_button("❌ 取消", use_container_width=True):
                            st.session_state.show_login = False
                            st.rerun()
                    
                    if register_submitted:
                        if register_username and register_password:
                            if register_password == confirm_password:
                                success, msg = add_user(register_username, register_password, selected_role)
                                if success:
                                    st.success("🎉 注册成功！")
                                    # 注册成功后自动登录
                                    st.session_state.logged_in = True
                                    st.session_state.username = register_username
                                    st.session_state.role = selected_role
                                    st.session_state.show_login = False
                                    st.rerun()
                                else:
                                    st.error(f"❌ {msg}")
                            else:
                                st.error("❌ 两次输入的密码不一致")
                        else:
                            st.warning("⚠️ 请输入完整的注册信息")
            
            st.markdown("</div>", unsafe_allow_html=True)

def get_experiment_stats():
    """获取实验作业统计数据（仅教师端使用）"""
    try:
        conn = sqlite3.connect('image_processing_platform.db')
        c = conn.cursor()
        
        # 获取总提交数
        c.execute("SELECT COUNT(*) FROM experiment_submissions")
        total_submissions = c.fetchone()[0]
        
        # 获取待批改数（status为'pending'）
        c.execute("SELECT COUNT(*) FROM experiment_submissions WHERE status = 'pending'")
        pending_count = c.fetchone()[0]
        
        # 获取已评分数（status为'graded'）
        c.execute("SELECT COUNT(*) FROM experiment_submissions WHERE status = 'graded'")
        graded_count = c.fetchone()[0]
        
        # 获取平均分
        c.execute("SELECT AVG(score) FROM experiment_submissions WHERE score > 0")
        avg_score_result = c.fetchone()[0]
        avg_score = round(avg_score_result, 1) if avg_score_result else 0
        
        conn.close()
        
        return {
            'total_submissions': total_submissions,
            'pending_count': pending_count,
            'graded_count': graded_count,
            'avg_score': avg_score
        }
    except Exception as e:
        print(f"获取作业统计数据失败: {str(e)}")
        return {
            'total_submissions': 0,
            'pending_count': 0,
            'graded_count': 0,
            'avg_score': 0
        }

def get_submission_by_username(username):
    """获取指定用户的提交情况"""
    try:
        conn = sqlite3.connect('image_processing_platform.db')
        c = conn.cursor()
        
        # 获取用户提交总数
        c.execute("SELECT COUNT(*) FROM experiment_submissions WHERE student_username = ?", (username,))
        user_total = c.fetchone()[0]
        
        # 获取用户已评分数
        c.execute("SELECT COUNT(*) FROM experiment_submissions WHERE student_username = ? AND status = 'graded'", (username,))
        user_graded = c.fetchone()[0]
        
        # 获取用户待批改数
        c.execute("SELECT COUNT(*) FROM experiment_submissions WHERE student_username = ? AND status = 'pending'", (username,))
        user_pending = c.fetchone()[0]
        
        # 获取用户平均分
        c.execute("SELECT AVG(score) FROM experiment_submissions WHERE student_username = ? AND score > 0", (username,))
        avg_score_result = c.fetchone()[0]
        user_avg_score = round(avg_score_result, 1) if avg_score_result else 0
        
        conn.close()
        
        return {
            'user_total': user_total,
            'user_graded': user_graded,
            'user_pending': user_pending,
            'user_avg_score': user_avg_score
        }
    except Exception as e:
        print(f"获取用户提交情况失败: {str(e)}")
        return {
            'user_total': 0,
            'user_graded': 0,
            'user_pending': 0,
            'user_avg_score': 0
        }

def main():
    # 初始化session_state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = ""
    if 'role' not in st.session_state:
        st.session_state.role = ""
    if 'show_login' not in st.session_state:
        st.session_state.show_login = False
    if 'selected_role' not in st.session_state:
        st.session_state.selected_role = "student"
    if 'show_change_password' not in st.session_state:
        st.session_state.show_change_password = False
    
    # 应用现代化CSS
    apply_modern_css()
    
    # 右上角用户区域
    render_user_area()
    
    # 主标题区域
    st.markdown("""
    <div class='modern-header'>
        <h1>融思政 - 数字图像处理实验平台</h1>
        <p class='subtitle'>融国家之情怀，思技术之正道，育时代之新人</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 修改密码对话框（优先显示）
    render_change_password_dialog()
    
    # 登录注册对话框
    render_login_dialog()
    
    # 渲染侧边栏
    render_sidebar()
    
    # 获取实时统计数据
    stats = get_user_stats()
    
    # 平台统计信息 - 使用真实数据，优秀作品数量固定为67
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👥 活跃用户", f"{stats['total_users']}", f"+{stats['student_count']}学生")
    with col2:
        st.metric("🔬 实验完成", f"{stats['experiment_count']}", "实时更新")
    with col3:
        st.metric("📚 思政感悟", f"{stats['reflection_count']}", "实时更新")
    with col4:
        st.metric("🏆 优秀作品", "67", "+15%")    
    
    # 三栏主要内容（调整为三栏以容纳实验作业提交模块）
    st.markdown("## 🚀 核心功能模块")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 图像处理实验室
        st.markdown("""
        <div class='modern-nav-card lab'>
            <div class='nav-icon'>🔬</div>
            <h3>图像处理实验室</h3>
            <p>进入专业的数字图像处理实验环境<br>体验现代化图像处理技术</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("进入实验室", key="lab_btn", use_container_width=True):
            if st.session_state.logged_in:
                st.switch_page("pages/1_🔬_图像处理实验室.py")
            else:
                st.warning("请先登录")
        
        # 学习资源中心
        st.markdown("""
        <div class='modern-nav-card resources'>
            <div class='nav-icon'>📚</div>
            <h3>学习资源中心</h3>
            <p>获取丰富的学习资料和教程<br>提升专业技能和理论水平</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("进入资源中心", key="resources_btn", use_container_width=True):
            if st.session_state.logged_in:
                st.switch_page("pages/2_📚_学习资源中心.py")
            else:
                st.warning("请先登录")
    
    with col2:
        # 我的思政足迹
        st.markdown("""
        <div class='modern-nav-card footprint'>
            <div class='nav-icon'>📝</div>
            <h3>我的思政足迹</h3>
            <p>记录个人学习成长轨迹<br>内化价值感悟与心得体会</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("查看足迹", key="footprint_btn", use_container_width=True):
            if st.session_state.logged_in:
                st.switch_page("pages/3_📝_我的思政足迹.py")
            else:
                st.warning("请先登录")
        
        # 成果展示
        st.markdown("""
        <div class='modern-nav-card achievement'>
            <div class='nav-icon'>🏆</div>
            <h3>成果展示</h3>
            <p>展示优秀作品和学习成果<br>分享技术实践与创新应用</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("查看成果", key="achievement_btn", use_container_width=True):
            if st.session_state.logged_in:
                st.switch_page("pages/4_🏆_成果展示.py")
            else:
                st.warning("请先登录")
    
    with col3:
        # 新增：实验作业提交
        st.markdown("""
        <div class='modern-nav-card submission'>
            <div class='nav-icon'>📤</div>
            <h3>实验作业提交</h3>
            <p>提交实验作业和报告<br>获取教师反馈与评分</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("提交作业", key="submission_btn", use_container_width=True):
            if st.session_state.logged_in:
                st.switch_page("pages/实验作业提交.py")
            else:
                st.warning("请先登录")
        
        # 根据用户角色显示不同的作业状态信息
        if st.session_state.logged_in:
            if st.session_state.role == "teacher":
                # 教师端：显示全局作业状态
                teacher_stats = get_experiment_stats()
                st.markdown("""
                <div style='background: linear-gradient(135deg, #f0fdf4, #dcfce7); 
                            padding: 25px; border-radius: 15px; margin-top: 20px;
                            border: 2px solid #10b981;'>
                    <h4 style='color: #10b981; text-align: center;'>📊 教师工作台</h4>
                    <p style='color: #065f46; text-align: center; font-size: 0.9rem;'>
                    📋 总提交: {total_submissions} 份<br>
                    ⏳ 待批改: {pending_count} 份<br>
                    ✅ 已批改: {graded_count} 份<br>
                    ⭐ 平均分: {avg_score} 分
                    </p>
                </div>
                """.format(
                    total_submissions=teacher_stats['total_submissions'],
                    pending_count=teacher_stats['pending_count'],
                    graded_count=teacher_stats['graded_count'],
                    avg_score=teacher_stats['avg_score']
                ), unsafe_allow_html=True)
                
            elif st.session_state.role == "student":
                # 学生端：显示个人作业状态
                student_stats = get_submission_by_username(st.session_state.username)
                st.markdown("""
                <div style='background: linear-gradient(135deg, #f0fdf4, #dcfce7); 
                            padding: 25px; border-radius: 15px; margin-top: 20px;
                            border: 2px solid #10b981;'>
                    <h4 style='color: #10b981; text-align: center;'>📊 我的作业</h4>
                    <p style='color: #065f46; text-align: center; font-size: 0.9rem;'>
                    📤 已提交: {user_total} 份<br>
                    ⏳ 待批改: {user_pending} 份<br>
                    ✅ 已批改: {user_graded} 份<br>
                    ⭐ 平均分: {user_avg_score} 分
                    </p>
                </div>
                """.format(
                    user_total=student_stats['user_total'],
                    user_pending=student_stats['user_pending'],
                    user_graded=student_stats['user_graded'],
                    user_avg_score=student_stats['user_avg_score']
                ), unsafe_allow_html=True)
    
    # 思政资源长廊
    st.markdown("---")
    st.markdown("<h2 style='text-align: center; color: #8B0000; margin-bottom: 40px; font-family: SimSun, serif;'>🇨🇳 思政资源长廊</h2>", unsafe_allow_html=True)
    
    # 引用卡片
    st.markdown("""
    <div style='
        background: linear-gradient(135deg, #fefaf0, #fff);
        padding: 40px;
        border-radius: 20px;
        border-left: 6px solid #8B0000;
        margin: 20px 0;
        box-shadow: 0 8px 25px rgba(139, 0, 0, 0.1);
        position: relative;
    '>
        <div style='
            font-size: 1.5rem;
            line-height: 1.8;
            margin-bottom: 25px;
            color: #8B0000;
            text-align: left;
            font-weight: 400;
            font-family: SimSun, serif;
        '>"科学工作者要有坚定的信念，要相信科学，要坚持真理，要勇于创新，要为人民服务。我们要把科学技术的最新成就，最快地应用到生产实践中去。"</div>
        <div style='
            text-align: left;
            color: #8B0000;
            font-weight: 600;
            font-size: 1.2rem;
            font-family: SimSun, serif;
        '>—— 钱学森</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 第一行科学家
    st.markdown('<div class="modern-scientists-container">', unsafe_allow_html=True)
    st.markdown('<div class="modern-scientists-row">', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class='modern-scientist-card'>
            <div class='modern-scientist-avatar'>钱</div>
            <div class='modern-scientist-info'>
                <h4>钱学森</h4>
                <div class='modern-scientist-desc'>中国航天事业奠基人</div>
                <div class='modern-achievement-badge'>五年归国路，十年两弹成</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class='modern-scientist-card'>
            <div class='modern-scientist-avatar'>袁</div>
            <div class='modern-scientist-info'>
                <h4>袁隆平</h4>
                <div class='modern-scientist-desc'>杂交水稻之父</div>
                <div class='modern-achievement-badge'>一粒种子，改变世界</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class='modern-scientist-card'>
            <div class='modern-scientist-avatar'>孙</div>
            <div class='modern-scientist-info'>
                <h4>孙家栋</h4>
                <div class='modern-scientist-desc'>北斗卫星导航系统总设计师</div>
                <div class='modern-achievement-badge'>一辈子一颗星</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class='modern-scientist-card'>
            <div class='modern-scientist-avatar'>黄</div>
            <div class='modern-scientist-info'>
                <h4>黄大年</h4>
                <div class='modern-scientist-desc'>地球物理学家</div>
                <div class='modern-achievement-badge'>振兴中华，乃我辈之责</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div></div>', unsafe_allow_html=True)

    # 第二行科学家（不同的人物）
    st.markdown('<div class="modern-scientists-container">', unsafe_allow_html=True)
    st.markdown('<div class="modern-scientists-row">', unsafe_allow_html=True)

    col5, col6, col7, col8 = st.columns(4)

    with col5:
        st.markdown("""
        <div class='modern-scientist-card'>
            <div class='modern-scientist-avatar'>邓</div>
            <div class='modern-scientist-info'>
                <h4>邓稼先</h4>
                <div class='modern-scientist-desc'>两弹一星元勋</div>
                <div class='modern-achievement-badge'>许身国威壮河山</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col6:
        st.markdown("""
        <div class='modern-scientist-card'>
            <div class='modern-scientist-avatar'>屠</div>
            <div class='modern-scientist-info'>
                <h4>屠呦呦</h4>
                <div class='modern-scientist-desc'>药学家</div>
                <div class='modern-achievement-badge'>青蒿素发现者</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col7:
        st.markdown("""
        <div class='modern-scientist-card'>
            <div class='modern-scientist-avatar'>南</div>
            <div class='modern-scientist-info'>
                <h4>南仁东</h4>
                <div class='modern-scientist-desc'>天文学家</div>
                <div class='modern-achievement-badge'>中国天眼之父</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col8:
        st.markdown("""
        <div class='modern-scientist-card'>
            <div class='modern-scientist-avatar'>吴</div>
            <div class='modern-scientist-info'>
                <h4>吴孟超</h4>
                <div class='modern-scientist-desc'>肝胆外科专家</div>
                <div class='modern-achievement-badge'>中国肝胆外科之父</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div></div>', unsafe_allow_html=True)
    
    # 新增：平台特色功能展示
    st.markdown("---")
    st.markdown("<h2 style='text-align: center; color: #8B0000; margin-bottom: 40px; font-family: SimSun, serif;'>✨ 平台特色功能</h2>", unsafe_allow_html=True)
    
    feature_col1, feature_col2, feature_col3, feature_col4 = st.columns(4)
    
    with feature_col1:
        st.markdown("""
        <div style='text-align: center; padding: 20px;'>
            <div style='font-size: 3rem; margin-bottom: 15px;'>🎯</div>
            <h4 style='color: #dc2626;'>精准思政融合</h4>
            <p style='color: #6b7280;'>将思政教育自然融入专业课程，实现价值引领与技术培养的完美结合</p>
        </div>
        """, unsafe_allow_html=True)
    
    with feature_col2:
        st.markdown("""
        <div style='text-align: center; padding: 20px;'>
            <div style='font-size: 3rem; margin-bottom: 15px;'>🚀</div>
            <h4 style='color: #dc2626;'>前沿技术实践</h4>
            <p style='color: #6b7280;'>基于Streamlit的现代化Web应用，提供沉浸式的图像处理学习体验</p>
        </div>
        """, unsafe_allow_html=True)
    
    with feature_col3:
        st.markdown("""
        <div style='text-align: center; padding: 20px;'>
            <div style='font-size: 3rem; margin-bottom: 15px;'>📊</div>
            <h4 style='color: #dc2626;'>学习数据分析</h4>
            <p style='color: #6b7280;'>实时追踪学习进度，个性化推荐资源，助力高效学习成长</p>
        </div>
        """, unsafe_allow_html=True)
    
    with feature_col4:
        st.markdown("""
        <div style='text-align: center; padding: 20px;'>
            <div style='font-size: 3rem; margin-bottom: 15px;'>📤</div>
            <h4 style='color: #dc2626;'>智能作业系统</h4>
            <p style='color: #6b7280;'>在线提交作业，及时获取反馈，提升学习效果与教学质量</p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
