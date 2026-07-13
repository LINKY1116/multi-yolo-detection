import os
from urllib.parse import quote_plus

class Config:
    """基础配置类"""
    # 数据库配置 - 使用 MySQL，可通过环境变量覆盖
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = os.getenv('MYSQL_PORT', '3306')
    MYSQL_DB = os.getenv('MYSQL_DB', 'yolo_detection')
    MYSQL_SOCKET = os.getenv('MYSQL_SOCKET', '').strip()
    if MYSQL_SOCKET:
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{MYSQL_USER}:{quote_plus(MYSQL_PASSWORD)}@localhost/{MYSQL_DB}"
            f"?unix_socket={quote_plus(MYSQL_SOCKET)}&charset=utf8mb4"
        )
    else:
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{MYSQL_USER}:{quote_plus(MYSQL_PASSWORD)}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4"
        )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask配置
    SECRET_KEY = 'yolo-detection-secret-key-2024'
    DEBUG = True
    
    # 文件上传配置
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    
    # YOLO模型配置
    YOLO_MODEL_PATH = 'models/yolov8n.pt'  # 默认使用 models 目录下的 YOLOv8n 模型
    DETECTION_CONFIDENCE = 0.25  # 检测置信度阈值

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-production-secret-key-here')

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URI', Config.SQLALCHEMY_DATABASE_URI)

# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 
