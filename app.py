

#  导入依赖
from flask import Flask, request, jsonify, send_file      # Flask
from flask_cors import CORS                               # 解决跨域问题

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os                                                 # 操作系统相关
import base64                                             # 用于 base64 编解码）
import io
from datetime import datetime                             # 日期时间
import json                                               # JSON 处理
import urllib.request
import urllib.error
from urllib.parse import quote_plus
import pymysql                                            # MySQL 数据库连接驱动

# 创建 Flask 应用
app = Flask(__name__)

# 配置 CORS用于跨域资源共享
CORS(app,
     origins="*",                                          # 允许所有域名跨域请求
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"], # 允许的 HTTP 方法
     allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
     supports_credentials=False)

# 在响应中添加 CORS 头
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'false')
    return response

# 数据库连接配置

MYSQL_USER = os.getenv('MYSQL_USER', 'root')                # 数据库用户名
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')  # 数据库密码，可通过环境变量覆盖
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')           # 数据库主机地址
MYSQL_PORT = os.getenv('MYSQL_PORT', '3306')                # MySQL 默认端口
MYSQL_DB = os.getenv('MYSQL_DB', 'yolo_detection')          # 数据库名称
MYSQL_SOCKET = os.getenv('MYSQL_SOCKET', '').strip()

# 拼接 SQLAlchemy 的数据库连接 URI  SQLAlchemy python库 使用操作对象的方式操作数据库
# 使得不需要直接手写sql语句
# 格式：mysql+pymysql://用户名:密码@主机:端口/数据库名?字符集
if MYSQL_SOCKET:
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"mysql+pymysql://{MYSQL_USER}:{quote_plus(MYSQL_PASSWORD)}@localhost/{MYSQL_DB}"
        f"?unix_socket={quote_plus(MYSQL_SOCKET)}&charset=utf8mb4"
    )
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"mysql+pymysql://{MYSQL_USER}:{quote_plus(MYSQL_PASSWORD)}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4"
    )
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Flask-SQLAlchemy 默认会追踪对数据库对象进行的每一次修改
# 这里将这个功能关闭  减少一部分内存开销

# 数据库连接池配置 用于避免频繁建立连接
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,   # 每次从连接池取出连接时先测试连接是否有效
    'pool_recycle': 3600,    # 连接存活时间单位是秒，超时会自动回收 这个连接
    'pool_size': 5,          # 连接池大小（注意 一个数据库的连接是有上限的 151）
    'max_overflow': 10,      # 最大溢出连接数 允许额外创建的临时连接的数量
}

# 上传文件与安全配置
app.config['UPLOAD_FOLDER'] = 'uploads'                     #上传文件的存放目录在哪里
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024        #最大上传文件为100MB
app.config['SECRET_KEY'] = 'yolo-detection-secret-key-2024'  # Flask 密钥

# 初始化 SQLAlchemy并将其连接到 Flask 应用
db = SQLAlchemy(app)

# 创建对应的目录 目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static', exist_ok=True)


# 数据库模型（ORM 实体类） Object-Relationship Mapping， 对象 - 关系映射。

class User(db.Model):
    """用户表（存储登录账号信息）"""
    id = db.Column(db.Integer, primary_key=True)
    #用户名
    username = db.Column(db.String(80), unique=True, nullable=False)
    # 用户的密码
    password = db.Column(db.String(255), nullable=False)
    # 用户的创建的时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class DetectionResult(db.Model):
    """检测结果表（存储每次检测的记录）"""
    id = db.Column(db.Integer, primary_key=True)
    # user_id 关联用户表的主键
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # detection_type：检测类型（图片/视频/摄像头），非空
    detection_type = db.Column(db.String(20), nullable=False)
    original_file = db.Column(db.String(255))               # 原始上传文件名
    result_file = db.Column(db.String(255))                 # 处理后的结果文件名
    # detections：长文本字段，存储 JSON 格式的检测详情
    detections = db.Column(db.Text)
    confidence = db.Column(db.Float)                        # 置信度
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 检测时间

#YOLO 模型加载
MODELS_DIR = 'models'
DEFAULT_MODEL_PATH = 'models/yolov8n.pt'
model = None                                 # 全局变量，保存加载的 YOLO 模型
current_model_path = DEFAULT_MODEL_PATH      # 当前使用的模型路径（默认 nano 版本）
cv2 = None
np = None
Image = None
YOLO = None

def ensure_vision_dependencies():
    """按需加载视觉检测依赖，避免数据库初始化时强制安装 PyTorch/YOLO。"""
    global cv2, np, Image, YOLO
    if cv2 is not None and np is not None and Image is not None and YOLO is not None:
        return
    try:
        import cv2 as cv2_module
        import numpy as np_module
        from PIL import Image as image_module
        from ultralytics import YOLO as yolo_module
    except ImportError as e:
        raise RuntimeError(f'视觉检测依赖未安装，请先安装 requirements.txt: {e}')
    cv2 = cv2_module
    np = np_module
    Image = image_module
    YOLO = yolo_module

def load_yolo_model(model_path=DEFAULT_MODEL_PATH):
    """加载指定的 YOLO 模型文件"""
    global model, current_model_path
    try:
        ensure_vision_dependencies()
        model = YOLO(model_path)
        current_model_path = model_path
        print(f"✅ YOLO模型加载成功: {model_path}")
        return True
    except Exception as e:
        print(f"❌ YOLO模型加载失败: {e}")
        return False

# 8. 模型文件管理辅助函数
def get_model_files(directory=MODELS_DIR):
    """扫描 models 目录，返回可用的模型文件列表"""
    model_extensions = ['.pt', '.onnx', '.torchscript']
    model_files = []
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    try:
        for root, dirs, files in os.walk(directory):
            for file in files:
                if any(file.lower().endswith(ext) for ext in model_extensions):
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    model_files.append({
                        'name': file,
                        'path': file_path,
                        'relative_path': os.path.relpath(file_path),
                        'size': file_size,
                        'size_mb': round(file_size / (1024 * 1024), 2),
                        'modified': os.path.getmtime(file_path)
                    })
    except Exception as e:
        print(f"扫描模型文件时出错: {e}")
    # 默认模型文件不存在时保留一个可加载的预置项，存在时直接使用扫描到的真实文件。
    scanned_paths = {item['path'] for item in model_files}
    pretrained_models = []
    if DEFAULT_MODEL_PATH not in scanned_paths:
        pretrained_models.append({
            'name': 'YOLOv8n (Nano)',
            'path': DEFAULT_MODEL_PATH,
            'relative_path': DEFAULT_MODEL_PATH,
            'size': 0,
            'size_mb': 6.2,
            'modified': 0,
            'pretrained': True
        })
    return pretrained_models + model_files

SCENARIO_MODEL_RULES = {
    'general': {
        'label': '通用检测',
        'default_model': DEFAULT_MODEL_PATH,
        'keywords': ['general', 'common', '通用']
    },
    'drone': {
        'label': '无人机检测',
        'keywords': ['drone', 'uav', '无人机', '飞行器']
    },
    'fire': {
        'label': '火灾检测',
        'keywords': ['fire', 'flame', 'smoke', '火灾', '火焰', '烟雾']
    },
    'flower': {
        'label': '花卉检测',
        'keywords': ['flower', 'rose', 'sunflower', 'tulip', 'daisy', '花卉', '花朵']
    },
    'pest': {
        'label': '病虫害检测',
        'keywords': ['pest', 'disease', 'leaf', 'plant', '病虫害', '病害', '虫害', '叶片']
    }
}

def get_models_for_scenario(scenario):
    """按命名规则返回某个场景可用的模型列表。"""
    scenario = scenario if scenario in SCENARIO_MODEL_RULES else 'general'
    rule = SCENARIO_MODEL_RULES[scenario]
    if scenario == 'general':
        general_models = [{
            'name': 'YOLOv8n (Nano)',
            'path': rule['default_model'],
            'relative_path': rule['default_model'],
            'size': 0,
            'size_mb': 6.2,
            'modified': 0,
            'pretrained': True
        }]
        custom_general = []
        for item in get_model_files(MODELS_DIR):
            if item.get('pretrained'):
                continue
            search_text = f"{item.get('name', '')} {item.get('path', '')}".lower()
            if any(keyword.lower() in search_text for keyword in rule['keywords']):
                custom_general.append(item)
        return general_models + custom_general

    scenario_models = []
    for item in get_model_files(MODELS_DIR):
        if item.get('pretrained'):
            continue
        search_text = f"{item.get('name', '')} {item.get('path', '')}".lower()
        if any(keyword.lower() in search_text for keyword in rule['keywords']):
            scenario_models.append(item)
    return scenario_models

def find_model_for_scenario(scenario):
    """按命名规则查找场景模型。通用场景固定优先使用默认模型。"""
    scenario = scenario if scenario in SCENARIO_MODEL_RULES else 'general'
    models_for_scenario = get_models_for_scenario(scenario)
    if models_for_scenario:
        return models_for_scenario[0]['path']
    rule = SCENARIO_MODEL_RULES[scenario]
    if scenario == 'general':
        return rule['default_model']
    return None

#9. mysql数据库自动创建
def ensure_database_exists():
    """如果不存在数据库的话在 MySQL 中创建数据库"""
    try:
        connect_kwargs = {
            'user': MYSQL_USER,
            'password': MYSQL_PASSWORD,
            'charset': 'utf8mb4'
        }
        if MYSQL_SOCKET:
            connect_kwargs['unix_socket'] = MYSQL_SOCKET
        else:
            connect_kwargs.update({
                'host': MYSQL_HOST,
                'port': int(MYSQL_PORT)
            })
        # 使用 pymysql 直接连接，执行建库语句
        conn = pymysql.connect(**connect_kwargs)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DB}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        cursor.close()
        conn.close()
        print(f"✅ 数据库 '{MYSQL_DB}' 已确保存在")
    except Exception as e:
        print(f"❌ 无法创建数据库，请检查MySQL连接: {e}")

def get_detection_confidence():
    """不同场景使用不同检测阈值。病虫害模型精度较低，演示时降低阈值。"""
    scenario = get_current_model_scenario()
    if scenario == 'pest':
        return 0.05
    return 0.25

def analyze_detections(detections, detection_type='image'):
    """对YOLO检测结果做结构化统计和复核建议"""
    total_objects = len(detections)
    class_counts = {}
    confidences = []
    low_confidence_threshold = 0.6

    for detection in detections:
        class_name = detection.get('class', 'unknown')
        confidence = float(detection.get('confidence', 0))
        class_counts[class_name] = class_counts.get(class_name, 0) + 1
        confidences.append(confidence)

    avg_confidence = round(sum(confidences) / len(confidences), 4) if confidences else 0
    max_confidence = round(max(confidences), 4) if confidences else 0
    low_confidence_count = len([conf for conf in confidences if conf < low_confidence_threshold])
    low_confidence_ratio = round(low_confidence_count / total_objects, 4) if total_objects else 0
    main_class = max(class_counts, key=class_counts.get) if class_counts else None

    review_required = (
        total_objects == 0 or
        avg_confidence < low_confidence_threshold or
        low_confidence_ratio > 0.3
    )

    if total_objects == 0:
        conclusion = '未检测到目标，建议更换图片或调整拍摄角度后重新检测。'
        reliability = '需复核'
    elif review_required:
        conclusion = f'本次检测共发现 {total_objects} 个目标，部分目标置信度偏低，建议人工复核检测结果。'
        reliability = '中等'
    else:
        conclusion = f'本次检测共发现 {total_objects} 个目标，主要类别为 {main_class}，整体置信度较高，结果较可靠。'
        reliability = '较高'

    return {
        'detection_type': detection_type,
        'total_objects': total_objects,
        'class_counts': class_counts,
        'main_class': main_class,
        'avg_confidence': avg_confidence,
        'max_confidence': max_confidence,
        'low_confidence_threshold': low_confidence_threshold,
        'low_confidence_count': low_confidence_count,
        'low_confidence_ratio': low_confidence_ratio,
        'review_required': review_required,
        'reliability': reliability,
        'conclusion': conclusion
    }

def analyze_video_detections(detections, processed_frames, total_frames, detection_interval):
    """对视频检测结果做结构化统计和视频维度分析"""
    analysis = analyze_detections(detections, 'video')
    detected_frames = sorted({detection.get('frame') for detection in detections if detection.get('frame') is not None})
    sampled_frame_count = len(range(0, processed_frames, detection_interval)) if processed_frames else 0
    avg_detections_per_sampled_frame = (
        round(len(detections) / sampled_frame_count, 4)
        if sampled_frame_count else 0
    )
    detected_frame_ratio = (
        round(len(detected_frames) / sampled_frame_count, 4)
        if sampled_frame_count else 0
    )

    if analysis['total_objects'] == 0:
        conclusion = '视频中未检测到目标，建议检查视频清晰度、拍摄角度或更换检测模型。'
    elif analysis['review_required']:
        conclusion = f'视频共处理 {processed_frames} 帧，累计检测到 {analysis["total_objects"]} 次目标，部分检测置信度偏低，建议人工复核关键片段。'
    else:
        conclusion = f'视频共处理 {processed_frames} 帧，累计检测到 {analysis["total_objects"]} 次目标，主要类别为 {analysis["main_class"]}，整体检测结果较稳定。'

    analysis.update({
        'processed_frames': processed_frames,
        'total_frames': total_frames,
        'detection_interval': detection_interval,
        'sampled_frame_count': sampled_frame_count,
        'detected_frame_count': len(detected_frames),
        'detected_frame_ratio': detected_frame_ratio,
        'avg_detections_per_sampled_frame': avg_detections_per_sampled_frame,
        'conclusion': conclusion
    })

    return analysis

def analyze_history_records(records):
    """对用户历史检测记录做统计分析"""
    total_records = len(records)
    type_counts = {'image': 0, 'video': 0, 'camera': 0}
    class_counts = {}
    record_confidences = []
    total_objects = 0
    empty_result_records = 0
    low_confidence_threshold = 0.6
    low_confidence_records = 0
    last_detection_at = None

    for record in records:
        type_counts[record.detection_type] = type_counts.get(record.detection_type, 0) + 1

        if record.confidence is not None:
            confidence = float(record.confidence)
            record_confidences.append(confidence)
            if confidence < low_confidence_threshold:
                low_confidence_records += 1

        if last_detection_at is None or record.created_at > last_detection_at:
            last_detection_at = record.created_at

        detections = []
        if record.detections:
            try:
                detections = json.loads(record.detections)
            except Exception:
                detections = []

        if not detections:
            empty_result_records += 1

        total_objects += len(detections)
        for detection in detections:
            class_name = detection.get('class', 'unknown')
            class_counts[class_name] = class_counts.get(class_name, 0) + 1

    avg_confidence = round(sum(record_confidences) / len(record_confidences), 4) if record_confidences else 0
    max_confidence = round(max(record_confidences), 4) if record_confidences else 0
    most_common_class = max(class_counts, key=class_counts.get) if class_counts else None
    low_confidence_ratio = round(low_confidence_records / total_records, 4) if total_records else 0

    review_required = total_records > 0 and (
        avg_confidence < low_confidence_threshold or
        low_confidence_ratio > 0.3 or
        empty_result_records > 0
    )

    if total_records == 0:
        conclusion = '暂无历史检测记录，完成检测后可生成历史分析。'
    elif review_required:
        conclusion = f'历史记录中共有 {total_records} 次检测，平均置信度偏低或存在空结果，建议重点复核低置信度记录。'
    else:
        conclusion = f'历史记录中共有 {total_records} 次检测，常见目标为 {most_common_class}，整体检测结果较稳定。'

    return {
        'total_records': total_records,
        'type_counts': type_counts,
        'total_objects': total_objects,
        'class_counts': class_counts,
        'most_common_class': most_common_class,
        'avg_confidence': avg_confidence,
        'max_confidence': max_confidence,
        'low_confidence_threshold': low_confidence_threshold,
        'low_confidence_records': low_confidence_records,
        'low_confidence_ratio': low_confidence_ratio,
        'empty_result_records': empty_result_records,
        'review_required': review_required,
        'last_detection_at': last_detection_at.isoformat() if last_detection_at else None,
        'conclusion': conclusion
    }

def summarize_detection_context(analysis, detections):
    """压缩检测上下文，避免把过长检测列表发给大模型"""
    detections = detections or []
    high_confidence_samples = sorted(
        detections,
        key=lambda item: item.get('confidence', 0),
        reverse=True
    )[:8]

    return {
        'analysis': analysis or {},
        'detection_count': len(detections),
        'top_detections': [
            {
                'class': item.get('class'),
                'confidence': round(float(item.get('confidence', 0)), 4),
                'bbox': item.get('bbox'),
                'frame': item.get('frame')
            }
            for item in high_confidence_samples
        ]
    }

def get_current_model_scenario():
    """根据当前模型路径推断检测场景，用于 AI 角色兜底切换。"""
    model_text = (current_model_path or '').lower()

    scenario_keywords = [
        (
            'pest',
            ['病虫害', '虫害', '病害', 'leaf', 'pest', 'disease', 'blight', 'rust', 'mildew', 'spot']
        ),
        (
            'flower',
            ['花卉', '花', 'flower', 'rose', 'sunflower', 'tulip', 'daisy', 'orchid', 'lily']
        ),
        (
            'fire',
            ['火灾', '火焰', '烟雾', 'fire', 'flame', 'smoke']
        ),
        (
            'drone',
            ['无人机', '飞行器', 'drone', 'uav']
        )
    ]

    for scenario, keywords in scenario_keywords:
        if any(keyword in model_text for keyword in keywords):
            return scenario
    return 'general'

def get_ai_role_config(scenario=None):
    """返回当前检测场景对应的 AI 角色配置。"""
    scenario = (scenario or '').strip() or get_current_model_scenario()
    configs = {
        'pest': {
            'role_name': '农业植保助手',
            'focus': '病害解释、可能影响、处理建议和人工复核提醒',
            'instruction': '你是农业植保助手，请从作物健康、病虫害风险、复核建议和处理方向进行解释。'
        },
        'flower': {
            'role_name': '花卉识别助手',
            'focus': '花卉类别、外观特征、常见用途、养护建议和识别可信度',
            'instruction': '你是花卉识别助手，请从花卉类别、外观特征、常见用途、养护建议和识别可信度进行解释。'
        },
        'fire': {
            'role_name': '安全预警助手',
            'focus': '火焰或烟雾风险、紧急程度、人工复核和处置建议',
            'instruction': '你是安全预警助手，请从火焰/烟雾风险、紧急程度、人工复核和处置建议进行解释。'
        },
        'drone': {
            'role_name': '低空安全监测助手',
            'focus': '目标出现情况、风险判断、监控建议和误检说明',
            'instruction': '你是低空安全监测助手，请从无人机目标出现情况、风险判断、监控建议和误检说明进行解释。'
        },
        'general': {
            'role_name': '通用目标检测助手',
            'focus': '检测概况、主要目标、可信度判断和复核建议',
            'instruction': '你是通用目标检测助手，请基于检测结果给出简洁、专业、面向普通用户的解释。'
        }
    }
    role_config = configs.get(scenario, configs['general']).copy()
    role_config['scenario'] = scenario
    role_config['current_model'] = current_model_path
    return role_config

def build_local_report(analysis):
    """大模型不可用时的本地兜底报告"""
    if not analysis:
        return '暂无可分析的检测结果。'

    total_objects = analysis.get('total_objects', 0)
    avg_confidence = round(analysis.get('avg_confidence', 0) * 100)
    max_confidence = round(analysis.get('max_confidence', 0) * 100)
    main_class = analysis.get('main_class') or '暂无主要类别'
    review_text = '建议人工复核。' if analysis.get('review_required') else '整体结果较可靠。'

    return (
        f'本次检测共发现 {total_objects} 个目标，主要类别为 {main_class}。'
        f'平均置信度约 {avg_confidence}%，最高置信度约 {max_confidence}%。'
        f'{review_text}'
    )

def build_project_assistant_local_answer(question):
    """小 Y 项目助手的大模型兜底回答。"""
    q = (question or '').lower()
    if any(keyword in q for keyword in ['模型', '命名', '名字']):
        return '模型命名用于自动切换：drone_yolov8.pt 对应无人机，fire_yolov8.pt 对应火灾，flower_yolov8.pt 对应花卉，pest_yolov8.pt 对应病虫害。通用检测使用默认 models/yolov8n.pt。'
    if any(keyword in q for keyword in ['ai', '角色', '问答']):
        return 'AI 会根据检测页选择的场景切换角色：无人机是低空安全监测助手，火灾是安全预警助手，花卉是花卉识别助手，病虫害是农业植保助手，通用检测是通用目标检测助手。'
    if any(keyword in q for keyword in ['检测', '流程', '怎么用']):
        return '使用流程是：先在模型管理上传模型，再到检测页选择场景和具体模型，然后上传图片/视频或打开摄像头，检测完成后查看结果并生成 AI 报告或继续问答。'
    if any(keyword in q for keyword in ['历史', '记录']):
        return '检测历史页面保存图片和视频检测记录，可以查看检测时间、文件、目标数量、置信度、结果预览，也支持下载和删除记录。'
    return '系统主要分为：首页、目标检测、模型管理、检测历史和 AI 分析。后端负责 YOLO 推理、文件处理、MySQL 存储和 DeepSeek 调用；前端负责上传、展示、模型切换和问答交互。'

def call_deepseek(messages, temperature=0.3, max_tokens=800, api_key=None):
    """调用DeepSeek快速对话模型"""
    api_key = api_key or os.getenv('DEEPSEEK_API_KEY')
    if not api_key and os.path.exists('.deepseek_api_key'):
        try:
            with open('.deepseek_api_key', 'r', encoding='utf-8') as key_file:
                api_key = key_file.read().strip()
        except Exception:
            api_key = None
    if not api_key:
        raise RuntimeError('未提供DeepSeek API Key')

    payload = {
        'model': os.getenv('DEEPSEEK_MODEL', 'deepseek-v4-flash'),
        'messages': messages,
        'temperature': temperature,
        'max_tokens': max_tokens,
        'stream': False
    }

    request_data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        'https://api.deepseek.com/chat/completions',
        data=request_data,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        },
        method='POST'
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            response_data = json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8', errors='ignore')
        raise RuntimeError(f'DeepSeek接口返回错误: {e.code} {error_body}')
    except Exception as e:
        raise RuntimeError(f'DeepSeek接口调用失败: {str(e)}')

    choices = response_data.get('choices', [])
    if not choices:
        raise RuntimeError('DeepSeek接口未返回有效内容')

    return choices[0].get('message', {}).get('content', '').strip()

# 辅助函数：用于进行文件类型检查
def allowed_file(filename):
    """检查上传的图片文件扩展名是否合法"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_video_file(filename):
    """检查上传的视频文件扩展名是否合法"""
    ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_model_file(filename):
    """检查上传的模型文件扩展名是否合法"""
    ALLOWED_EXTENSIONS = {'pt', 'onnx', 'torchscript', 'engine'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# API 路由
# 以下每一个 @app.route 定义了一个 URL 接口，对应前端请求

@app.route('/api/<path:path>', methods=['OPTIONS'])
def options(path):
    """处理所有 /api/ 路由的 OPTIONS"""
    return '', 200

@app.route('/api/health', methods=['GET'])
def health_check():
    """用于确认后端服务是否正常运行"""
    return jsonify({
        'success': True,
        'message': 'YOLO检测识别系统运行正常',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/login', methods=['POST'])
def login():
    """登录接口：接收 JSON 格式的用户名和密码，验证后返回登录状态"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    # 查询用户表中是否存在该用户名和密码的组合
    user = User.query.filter_by(username=username, password=password).first()
    if user:
        return jsonify({
            'success': True,
            'message': '登录成功',
            'user': {
                'id': user.id,
                'username': user.username
            }
        })
    else:
        return jsonify({
            'success': False,
            'message': '用户名或密码错误'
        }), 401

@app.route('/api/register', methods=['POST'])
def register():
    """注册接口：接收 JSON 格式的用户名和密码，插入新用户记录"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    # 检查用户名是否已存在
    if User.query.filter_by(username=username).first():
        return jsonify({
            'success': False,
            'message': '用户名已存在'
        }), 400
    user = User(username=username, password=password)
    db.session.add(user)
    db.session.commit()                                     # 提交事务 持久化到数据库
    return jsonify({
        'success': True,
        'message': '注册成功'
    })

@app.route('/api/reset_password', methods=['POST'])
def reset_password():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'success': False, 'message': '用户名和新密码不能为空'})

    if len(password) < 6:
        return jsonify({'success': False, 'message': '密码长度不能少于6位'})

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'})

    user.password = password
    db.session.commit()
    return jsonify({'success': True, 'message': '密码重置成功，请使用新密码登录'})


@app.route('/api/detect_image', methods=['POST'])
def detect_image():
    """图片检测接口：接收上传的图片，调用 YOLO 进行目标检测，返回检测框和结果图片"""
    try:
        ensure_vision_dependencies()
    except RuntimeError as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    if model is None:
        return jsonify({'success': False, 'message': 'YOLO模型未加载'}), 500
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有上传文件'}), 400
    file = request.files['file']
    user_id = request.form.get('user_id', 1)                # 默认用户ID为1
    if file.filename == '':
        return jsonify({'success': False, 'message': '没有选择文件'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)           # 安全处理文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)                                 # 保存上传的文件
        try:
            # 使用 YOLO 模型检测图片
            results = model(filepath, conf=get_detection_confidence())
            detections = []
            img = cv2.imread(filepath)                      # 读取原始图片
            for r in results:
                boxes = r.boxes
                if boxes is not None:
                    for box in boxes:
                        # 获取检测框坐标、置信度、类别索引
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        conf = box.conf[0].cpu().numpy()
                        cls = box.cls[0].cpu().numpy()
                        detections.append({
                            'class': model.names[int(cls)],
                            'confidence': float(conf),
                            'bbox': [float(x1), float(y1), float(x2), float(y2)]
                        })
                        # 在图片上绘制红色框和标签
                        cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                        cv2.putText(img, f'{model.names[int(cls)]}: {conf:.2f}',
                                  (int(x1), int(y1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            # 保存检测结果图片
            result_filename = 'result_' + filename
            result_filepath = os.path.join('static', result_filename)
            cv2.imwrite(result_filepath, img)
            analysis = analyze_detections(detections, 'image')

            # 将检测记录存入数据库
            detection_result = DetectionResult(
                user_id=user_id,
                detection_type='image',
                original_file=filename,
                result_file=result_filename,
                detections=json.dumps(detections),
                confidence=max([d['confidence'] for d in detections]) if detections else 0
            )
            db.session.add(detection_result)
            db.session.commit()
            return jsonify({
                'success': True,
                'message': '检测完成',
                'detections': detections,
                'result_image': f'/static/{result_filename}',
                'detection_count': len(detections),
                'analysis': analysis
            })
        except Exception as e:
            return jsonify({'success': False, 'message': f'检测失败: {str(e)}'}), 500
    return jsonify({'success': False, 'message': '不支持的文件格式'}), 400

@app.route('/api/detect_video', methods=['POST'])
def detect_video():
    """视频检测接口：接收上传的视频，逐帧检测并绘制检测框，返回处理后的视频和检测历史"""
    try:
        ensure_vision_dependencies()
    except RuntimeError as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    if model is None:
        return jsonify({'success': False, 'message': 'YOLO模型未加载'}), 500
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有上传文件'}), 400
    file = request.files['file']
    user_id = request.form.get('user_id', 1)
    if file.filename == '':
        return jsonify({'success': False, 'message': '没有选择文件'}), 400
    if file and allowed_video_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        original_name, _ = os.path.splitext(filename)
        filename = timestamp + original_name + '.mp4'       # 统一输出为 mp4 格式
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], timestamp + secure_filename(file.filename))
        file.save(filepath)
        try:
            cap = cv2.VideoCapture(filepath)
            if not cap.isOpened():
                return jsonify({'success': False, 'message': '无法打开视频文件'}), 400
            # 获取视频属性
            fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if width <= 0 or height <= 0:
                return jsonify({'success': False, 'message': '视频尺寸无效'}), 400
            result_filename = 'result_' + filename
            result_filepath = os.path.join('static', result_filename)
            # 尝试多种编码器，确保输出的 mp4 能在浏览器播放
            encoders = [
                cv2.VideoWriter_fourcc(*'avc1'),
                cv2.VideoWriter_fourcc(*'mp4v'),
                cv2.VideoWriter_fourcc(*'XVID'),
            ]
            out = None
            for fourcc in encoders:
                try:
                    out = cv2.VideoWriter(result_filepath, fourcc, fps, (width, height))
                    if out.isOpened():
                        break
                    else:
                        out.release()
                        out = None
                except:
                    if out: out.release()
                    out = None
            if out is None:
                cap.release()
                return jsonify({'success': False, 'message': '无法创建输出视频文件'}), 500
            all_detections = []
            current_detections = []
            detection_interval = 10          # 每10帧检测一次，提升速度
            detection_hold_frames = 30       # 检测框保留30帧
            last_detection_frame = -detection_hold_frames
            frame_count = 0
            while True:
                ret, frame = cap.read()
                if not ret: break
                # 每隔 detection_interval 帧进行一次 YOLO 检测
                if frame_count % detection_interval == 0:
                    try:
                        results = model(frame, conf=get_detection_confidence())
                        last_detection_frame = frame_count
                        current_detections = []
                        for r in results:
                            if r.boxes is not None:
                                for box in r.boxes:
                                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                                    conf = box.conf[0].cpu().numpy()
                                    cls = box.cls[0].cpu().numpy()
                                    detection_info = {
                                        'frame': frame_count,
                                        'class': model.names[int(cls)],
                                        'confidence': float(conf),
                                        'bbox': [float(x1), float(y1), float(x2), float(y2)]
                                    }
                                    all_detections.append(detection_info)
                                    current_detections.append({
                                        'bbox': [x1, y1, x2, y2],
                                        'class': model.names[int(cls)],
                                        'confidence': conf,
                                        'detection_frame': frame_count
                                    })
                    except Exception as e:
                        print(f"⚠️ 帧 {frame_count} 检测失败: {e}")
                # 如果超过保持帧数，清除过期的检测框
                if frame_count - last_detection_frame > detection_hold_frames:
                    current_detections = []
                # 在当前帧上绘制检测框（保留透明度渐变效果）
                for det in current_detections:
                    x1, y1, x2, y2 = det['bbox']
                    frame_diff = frame_count - det['detection_frame']
                    alpha = max(0.3, 1.0 - (frame_diff / detection_hold_frames) * 0.7)
                    color = (0, int(255 * alpha), 0)
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                    label = f"{det['class']}: {det['confidence']:.2f}"
                    label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
                    overlay = frame.copy()
                    cv2.rectangle(overlay, (int(x1), int(y1) - label_size[1] - 10),
                                  (int(x1) + label_size[0], int(y1)), color, -1)
                    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
                    cv2.putText(frame, label, (int(x1), int(y1) - 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
                out.write(frame)
                frame_count += 1
                if frame_count % 500 == 0:   # 定期清理过期检测框，节省内存
                    current_detections = [d for d in current_detections
                                          if frame_count - d['detection_frame'] <= detection_hold_frames]
            cap.release()
            out.release()
            if not os.path.exists(result_filepath) or os.path.getsize(result_filepath) < 1024:
                return jsonify({'success': False, 'message': '视频生成失败'}), 500
            analysis = analyze_video_detections(
                all_detections,
                frame_count,
                total_frames,
                detection_interval
            )
            # 将检测记录存入数据库
            detection_result = DetectionResult(
                user_id=user_id, detection_type='video',
                original_file=os.path.basename(filepath),
                result_file=result_filename,
                detections=json.dumps(all_detections),
                confidence=max([d['confidence'] for d in all_detections]) if all_detections else 0
            )
            db.session.add(detection_result)
            db.session.commit()
            return jsonify({
                'success': True, 'message': '视频检测完成',
                'detections': all_detections,
                'result_video': f'/static/{result_filename}',
                'detection_count': len(all_detections),
                'processed_frames': frame_count,
                'total_detections': len(all_detections),
                'analysis': analysis
            })
        except Exception as e:
            print(f"❌ 视频处理异常: {e}")
            return jsonify({'success': False, 'message': f'视频检测失败: {str(e)}'}), 500
    return jsonify({'success': False, 'message': '不支持的视频格式'}), 400

@app.route('/api/detect_camera', methods=['POST'])
def detect_camera():
    """摄像头检测接口：返回摄像头配置信息（实际由前端调用摄像头，后端逐帧处理）"""
    user_id = request.json.get('user_id', 1)
    return jsonify({
        'success': True,
        'message': '摄像头检测模式已启动',
        'camera_config': {
            'fps': 30,
            'resolution': '640x480'
        }
    })

@app.route('/api/process_frame', methods=['POST'])
def process_frame():
    """前端实时传输摄像头单帧，后端进行 YOLO 检测并返回检测结果"""
    try:
        ensure_vision_dependencies()
        if model is None:
            return jsonify({'success': False, 'message': 'YOLO模型未加载'}), 500
        data = request.get_json()
        image_data = data.get('image')
        # 去掉 base64 头部信息，只取数据部分
        image_data = image_data.split(',')[1]
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        results = model(frame, conf=get_detection_confidence())
        detections = []
        for r in results:
            if r.boxes is not None:
                for box in r.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = box.conf[0].cpu().numpy()
                    cls = box.cls[0].cpu().numpy()
                    detections.append({
                        'class': model.names[int(cls)],
                        'confidence': float(conf),
                        'bbox': [float(x1), float(y1), float(x2), float(y2)]
                    })
        return jsonify({'success': True, 'detections': detections})
    except Exception as e:
        return jsonify({'success': False, 'message': f'帧处理失败: {str(e)}'}), 500

@app.route('/api/analysis/history/<int:user_id>')
def get_history_analysis(user_id):
    """获取用户历史检测智能分析"""
    try:
        records = DetectionResult.query.filter_by(user_id=user_id).all()
        analysis = analyze_history_records(records)

        return jsonify({
            'success': True,
            'analysis': analysis
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'获取历史分析失败: {str(e)}'}), 500

@app.route('/api/analysis/report', methods=['POST'])
def generate_ai_report():
    """基于当前检测结果生成自然语言报告"""
    try:
        data = request.get_json() or {}
        analysis = data.get('analysis') or {}
        detections = data.get('detections') or []
        api_key = (data.get('api_key') or '').strip()
        scenario = data.get('scenario') or data.get('model_scenario') or ''
        detection_type = analysis.get('detection_type') or data.get('detection_type') or 'image'
        context = summarize_detection_context(analysis, detections)
        role_config = get_ai_role_config(scenario)

        messages = [
            {
                'role': 'system',
                'content': (
                    f'你是目标检测系统中的{role_config["role_name"]}。'
                    f'{role_config["instruction"]}'
                    f'回答重点包括：{role_config["focus"]}。'
                    '报告包含：检测概况、可信度判断、主要目标、复核建议。'
                    '不要编造没有出现在数据中的目标。'
                )
            },
            {
                'role': 'user',
                'content': json.dumps({
                    'detection_type': detection_type,
                    'role_config': role_config,
                    'context': context
                }, ensure_ascii=False)
            }
        ]

        try:
            report = call_deepseek(messages, temperature=0.2, max_tokens=700, api_key=api_key)
            ai_enabled = True
            message = 'AI报告生成成功'
        except Exception as e:
            report = build_local_report(analysis)
            ai_enabled = False
            message = f'大模型暂不可用，已生成本地基础报告：{str(e)}'

        return jsonify({
            'success': True,
            'report': report,
            'ai_enabled': ai_enabled,
            'message': message
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'生成AI报告失败: {str(e)}'}), 500

@app.route('/api/analysis/chat', methods=['POST'])
def chat_with_detection_assistant():
    """围绕当前检测结果进行多轮问答"""
    try:
        data = request.get_json() or {}
        user_message = (data.get('message') or '').strip()
        if not user_message:
            return jsonify({'success': False, 'message': '请输入问题'}), 400

        analysis = data.get('analysis') or {}
        detections = data.get('detections') or []
        history_messages = data.get('messages') or []
        api_key = (data.get('api_key') or '').strip()
        scenario = data.get('scenario') or data.get('model_scenario') or ''
        context = summarize_detection_context(analysis, detections)
        role_config = get_ai_role_config(scenario)

        messages = [
            {
                'role': 'system',
                'content': (
                    f'你是YOLO目标检测系统里的{role_config["role_name"]}。'
                    f'{role_config["instruction"]}'
                    f'回答重点包括：{role_config["focus"]}。'
                    '你只能根据当前检测结果、统计分析和用户问题进行回答。'
                    '如果数据不足，要明确说明不能确定，并给出合理的复核或拍摄建议。'
                    '回答保持简洁，不使用思考过程。'
                )
            },
            {
                'role': 'system',
                'content': '当前检测上下文：' + json.dumps({
                    'role_config': role_config,
                    'context': context
                }, ensure_ascii=False)
            }
        ]

        for item in history_messages[-8:]:
            role = item.get('role')
            content = item.get('content')
            if role in ['user', 'assistant'] and content:
                messages.append({'role': role, 'content': content})

        messages.append({'role': 'user', 'content': user_message})

        try:
            reply = call_deepseek(messages, temperature=0.4, max_tokens=600, api_key=api_key)
            ai_enabled = True
            message = '回答生成成功'
        except Exception as e:
            reply = (
                build_local_report(analysis) +
                ' 目前大模型问答不可用，请检查 DEEPSEEK_API_KEY 配置或网络连接。'
            )
            ai_enabled = False
            message = f'大模型暂不可用，已返回本地回答：{str(e)}'

        return jsonify({
            'success': True,
            'reply': reply,
            'ai_enabled': ai_enabled,
            'message': message
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'智能问答失败: {str(e)}'}), 500

@app.route('/api/project_assistant/chat', methods=['POST'])
def chat_with_project_assistant():
    """小 Y 项目助手：回答系统功能、模块分布和使用方式。"""
    try:
        data = request.get_json() or {}
        question = (data.get('message') or '').strip()
        if not question:
            return jsonify({'success': False, 'message': '请输入问题'}), 400

        project_context = {
            'project_name': '多场景 YOLO 智能视觉检测平台',
            'frontend_pages': ['首页', '目标检测', '检测历史', '模型管理', '小Y检测助手'],
            'backend_modules': ['用户登录注册', 'MySQL数据存储', '图片检测', '视频检测', '摄像头检测', '模型管理', 'AI报告', '智能问答'],
            'scenes': {
                'general': '通用检测，默认使用 models/yolov8n.pt，对应通用目标检测助手',
                'drone': '无人机检测，推荐模型名 drone_yolov8.pt，对应低空安全监测助手',
                'fire': '火灾检测，推荐模型名 fire_yolov8.pt，对应安全预警助手',
                'flower': '花卉检测，推荐模型名 flower_yolov8.pt，对应花卉识别助手',
                'pest': '病虫害检测，推荐模型名 pest_yolov8.pt，对应农业植保助手'
            },
            'workflow': '上传模型 -> 检测页选择场景 -> 选择具体模型 -> 上传图片/视频或摄像头检测 -> 查看结果 -> AI报告或问答'
        }

        messages = [
            {
                'role': 'system',
                'content': (
                    '你是“小 Y 检测助手”，只回答本项目的功能说明、页面分布、使用流程、模型命名规则、'
                    'AI角色切换、前后端职责和课程答辩相关问题。'
                    '回答要中文、简洁、适合普通用户理解。不要编造项目没有的功能。'
                )
            },
            {
                'role': 'user',
                'content': json.dumps({
                    'project_context': project_context,
                    'question': question
                }, ensure_ascii=False)
            }
        ]

        try:
            reply = call_deepseek(messages, temperature=0.3, max_tokens=600)
            return jsonify({'success': True, 'reply': reply, 'ai_enabled': True, 'message': '小Y智能回答生成成功'})
        except Exception as e:
            return jsonify({
                'success': True,
                'reply': build_project_assistant_local_answer(question),
                'ai_enabled': False,
                'message': f'DeepSeek暂不可用，已返回本地回答：{str(e)}'
            })

    except Exception as e:
        return jsonify({'success': False, 'message': f'小Y问答失败: {str(e)}'}), 500

@app.route('/api/history/<int:user_id>')
def get_history(user_id):
    """根据用户ID获取其所有检测历史记录（按时间倒序）"""
    results = DetectionResult.query.filter_by(user_id=user_id).order_by(DetectionResult.created_at.desc()).all()
    history = []
    for r in results:
        history.append({
            'id': r.id,
            'detection_type': r.detection_type,
            'original_file': r.original_file,
            'result_file': r.result_file,
            'detections': json.loads(r.detections) if r.detections else [],
            'confidence': r.confidence,
            'created_at': r.created_at.isoformat()
        })
    return jsonify({'success': True, 'history': history})

@app.route('/api/history/delete/<int:record_id>', methods=['DELETE'])
def delete_history_record(record_id):
    """删除单条检测记录，同时删除相关文件"""
    record = DetectionResult.query.get(record_id)
    if not record:
        return jsonify({'success': False, 'message': '记录不存在'}), 404
    # 删除硬盘上的结果文件和原始文件
    if record.result_file:
        path = os.path.join('static', record.result_file)
        if os.path.exists(path):
            os.remove(path)
    if record.original_file:
        path = os.path.join(app.config['UPLOAD_FOLDER'], record.original_file)
        if os.path.exists(path):
            os.remove(path)
    db.session.delete(record)
    db.session.commit()
    return jsonify({'success': True, 'message': '历史记录删除成功'})

@app.route('/api/history/batch-delete', methods=['DELETE'])
def batch_delete_history():
    """批量删除检测历史记录"""
    data = request.get_json()
    record_ids = data.get('record_ids', [])
    user_id = data.get('user_id')
    if not record_ids:
        return jsonify({'success': False, 'message': '未指定要删除的记录'}), 400
    deleted_count = 0
    for rid in record_ids:
        record = DetectionResult.query.filter_by(id=rid, user_id=user_id).first()
        if not record:
            continue
        if record.result_file:
            path = os.path.join('static', record.result_file)
            if os.path.exists(path):
                os.remove(path)
        if record.original_file:
            path = os.path.join(app.config['UPLOAD_FOLDER'], record.original_file)
            if os.path.exists(path):
                os.remove(path)
        db.session.delete(record)
        deleted_count += 1
    db.session.commit()
    return jsonify({'success': True, 'message': f'成功删除 {deleted_count} 条记录'})

@app.route('/api/history/clear/<int:user_id>', methods=['DELETE'])
def clear_user_history(user_id):
    """清空指定用户的所有检测历史"""
    records = DetectionResult.query.filter_by(user_id=user_id).all()
    if not records:
        return jsonify({'success': True, 'message': '没有需要清空的记录'})
    deleted_count = 0
    for r in records:
        if r.result_file:
            path = os.path.join('static', r.result_file)
            if os.path.exists(path):
                os.remove(path)
        if r.original_file:
            path = os.path.join(app.config['UPLOAD_FOLDER'], r.original_file)
            if os.path.exists(path):
                os.remove(path)
        db.session.delete(r)
        deleted_count += 1
    db.session.commit()
    return jsonify({'success': True, 'message': f'成功清空所有历史记录，共删除 {deleted_count} 条'})

@app.route('/api/models', methods=['GET'])
def get_models():
    """获取可用的模型列表（包括预训练模型和用户上传的模型）"""
    models_dir = request.args.get('dir', MODELS_DIR)
    model_files = get_model_files(models_dir)
    return jsonify({
        'success': True,
        'models': model_files,
        'current_model': current_model_path,
        'models_directory': models_dir
    })

@app.route('/api/models/load', methods=['POST'])
def load_model():
    """切换当前使用的 YOLO 模型"""
    data = request.get_json()
    model_path = data.get('model_path')
    if not model_path:
        return jsonify({'success': False, 'message': '未指定模型路径'}), 400
    if not os.path.exists(model_path):
        return jsonify({'success': False, 'message': f'模型文件不存在: {model_path}'}), 404
    success = load_yolo_model(model_path)
    if success:
        return jsonify({
            'success': True,
            'message': f'模型加载成功: {model_path}',
            'current_model': current_model_path,
            'model_info': {
                'path': current_model_path,
                'classes': list(model.names.values()) if model else [],
                'class_count': len(model.names) if model else 0
            }
        })
    return jsonify({'success': False, 'message': '模型加载失败'}), 500

@app.route('/api/models/current', methods=['GET'])
def get_current_model():
    """获取当前模型的基本信息"""
    return jsonify({
        'success': True,
        'model_info': {
            'path': current_model_path,
            'loaded': model is not None,
            'classes': list(model.names.values()) if model else [],
            'class_count': len(model.names) if model else 0
        }
    })

@app.route('/api/models/scenario/<scenario>', methods=['GET'])
def get_scenario_models(scenario):
    """获取某个检测场景下可自动匹配的模型列表。"""
    if scenario not in SCENARIO_MODEL_RULES:
        return jsonify({'success': False, 'message': f'未知检测场景: {scenario}'}), 400
    rule = SCENARIO_MODEL_RULES[scenario]
    models_for_scenario = get_models_for_scenario(scenario)
    return jsonify({
        'success': True,
        'scenario': scenario,
        'scenario_label': rule['label'],
        'models': models_for_scenario,
        'expected_keywords': rule['keywords'],
        'current_model': current_model_path
    })

@app.route('/api/models/load_by_scenario', methods=['POST'])
def load_model_by_scenario():
    """按检测场景自动加载对应模型。"""
    data = request.get_json() or {}
    scenario = data.get('scenario') or 'general'
    if scenario not in SCENARIO_MODEL_RULES:
        return jsonify({'success': False, 'message': f'未知检测场景: {scenario}'}), 400

    model_path = data.get('model_path') or find_model_for_scenario(scenario)
    if not model_path:
        rule = SCENARIO_MODEL_RULES[scenario]
        return jsonify({
            'success': False,
            'message': (
                f'未找到{rule["label"]}模型。请在模型管理中上传文件名包含 '
                f'{"/".join(rule["keywords"][:4])} 的模型文件。'
            ),
            'scenario': scenario,
            'scenario_label': rule['label'],
            'expected_keywords': rule['keywords']
        }), 404
    if not os.path.exists(model_path):
        return jsonify({'success': False, 'message': f'模型文件不存在: {model_path}'}), 404

    success = load_yolo_model(model_path)
    if success:
        rule = SCENARIO_MODEL_RULES[scenario]
        return jsonify({
            'success': True,
            'message': f'已切换为{rule["label"]}，加载模型: {model_path}',
            'scenario': scenario,
            'scenario_label': rule['label'],
            'current_model': current_model_path,
            'model_info': {
                'path': current_model_path,
                'classes': list(model.names.values()) if model else [],
                'class_count': len(model.names) if model else 0
            }
        })
    return jsonify({'success': False, 'message': f'模型加载失败: {model_path}'}), 500

@app.route('/api/models/upload', methods=['POST'])
def upload_model():
    """上传用户自定义的 YOLO 模型文件"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有上传文件'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': '没有选择文件'}), 400
    if not allowed_model_file(file.filename):
        return jsonify({'success': False, 'message': '不支持的模型文件格式'}), 400
    models_dir = MODELS_DIR
    os.makedirs(models_dir, exist_ok=True)
    filename = secure_filename(file.filename)
    unique_filename = datetime.now().strftime('%Y%m%d_%H%M%S_') + filename
    filepath = os.path.join(models_dir, unique_filename)
    file.save(filepath)
    return jsonify({
        'success': True, 'message': '模型文件上传成功',
        'file_path': filepath, 'filename': unique_filename
    })

@app.route('/api/models/delete', methods=['DELETE'])
def delete_model():
    """删除指定的模型文件（不能删除当前正在使用的模型）"""
    data = request.get_json()
    model_path = data.get('model_path')
    if not model_path:
        return jsonify({'success': False, 'message': '未指定模型路径'}), 400
    if model_path == current_model_path:
        return jsonify({'success': False, 'message': '不能删除当前正在使用的模型'}), 400
    if os.path.exists(model_path):
        os.remove(model_path)
        return jsonify({'success': True, 'message': f'模型文件删除成功: {model_path}'})
    return jsonify({'success': False, 'message': '模型文件不存在'}), 404

@app.route('/static/<filename>')
def static_files(filename):
    """返回 static 目录下的文件（如检测结果图片、视频）"""
    return send_file(os.path.join('static', filename))

#应用启动入口
if __name__ == '__main__':
    #  先确保 MySQL 数据库存在 如果没有就先自动创建
    ensure_database_exists()
    #  在应用上下文中创建所有数据库表
    with app.app_context():
        db.create_all()
        # 创建默认管理员用户 如果不存在的话
        if not User.query.filter_by(username='admin').first():
            admin_user = User(username='admin', password='admin123')
            db.session.add(admin_user)
            db.session.commit()
            print("✅ 创建默认管理员用户: admin / admin123")
    #  加载默认的 YOLO 模型
    load_yolo_model()
    print("🚀 启动YOLO检测识别系统...")
    db_location = MYSQL_SOCKET if MYSQL_SOCKET else f"{MYSQL_HOST}:{MYSQL_PORT}"
    print(f"📊 数据库: MySQL ({db_location}/{MYSQL_DB})")
    print("🌐 访问地址: http://localhost:5001")
    print("👤 默认账号: admin / admin123")
    #  启动 Flask 服务器
    app.run(debug=True, host='0.0.0.0', port=5001, use_reloader=False)





