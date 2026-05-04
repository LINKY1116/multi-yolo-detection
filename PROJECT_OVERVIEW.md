# YOLO检测识别系统项目介绍

## 项目简介

本项目是一个基于 YOLOv8 的目标检测识别系统，支持图片检测、视频检测和摄像头实时检测。系统采用前后端分离架构，后端负责模型推理、文件处理、数据库记录和智能分析，前端负责用户交互、结果展示、历史记录管理和模型管理。

系统面向普通用户提供可视化目标检测能力。用户登录后可以上传图片或视频，系统自动调用 YOLO 模型识别目标，并在结果图像或视频上绘制检测框、类别和置信度。同时系统会保存检测历史，方便用户查看、下载和管理检测结果。

## 技术栈

后端：

- Flask：提供 Web API 服务
- Flask-CORS：处理前后端跨域请求
- Flask-SQLAlchemy：操作 SQLite 数据库
- SQLite：保存用户信息和检测历史
- Ultralytics YOLOv8：目标检测模型推理
- OpenCV：图片和视频处理、检测框绘制
- Pillow：图片格式处理
- DeepSeek API：生成自然语言检测报告和智能问答

前端：

- Vue 3：前端页面框架
- Vue Router：页面路由管理
- Vuex：用户状态和检测数据管理
- Element Plus：UI 组件库
- Axios / fetch：调用后端接口

## 项目结构

```text
web_yolo_recong/
├── app.py
├── config.py
├── init_db.py
├── check_env.py
├── requirements.txt
├── yolov8n.pt
├── models/
├── uploads/
├── static/
├── instance/
└── frontend/
    ├── package.json
    ├── vue.config.js
    ├── public/
    └── src/
        ├── main.js
        ├── App.vue
        ├── router/
        ├── store/
        └── views/
```

## 主要文件说明

`app.py` 是后端主程序，包含 Flask 应用、数据库模型、登录注册接口、图片检测接口、视频检测接口、摄像头帧检测接口、历史记录接口、模型管理接口和 AI 智能分析接口。

`config.py` 是配置文件，定义数据库路径、上传目录、模型路径、置信度阈值等配置项。

`init_db.py` 是数据库初始化脚本，用于创建数据库表和默认用户。

`check_env.py` 是环境检查脚本，用于检查 Python、pip、Node.js、npm 等环境是否安装。

`requirements.txt` 是 Python 依赖清单。

`yolov8n.pt` 是默认 YOLOv8n 预训练模型文件。

`models/` 用于保存用户上传的自定义模型文件。

`uploads/` 用于保存用户上传的原始图片或视频。

`static/` 用于保存检测后的结果图片或视频。

`instance/yolo_detection.db` 是 SQLite 数据库文件。

`frontend/src/views/Detection.vue` 是目标检测页面，负责图片、视频、摄像头检测的前端交互和结果展示。

`frontend/src/views/History.vue` 是检测历史页面，负责展示历史记录、详情、下载、删除和历史智能分析。

`frontend/src/views/ModelManager.vue` 是模型管理页面，负责模型列表、上传、加载和删除。

`frontend/src/views/Login.vue` 是登录注册页面。

`frontend/src/views/Dashboard.vue` 是系统主布局页面。

`frontend/src/router/index.js` 是前端路由配置。

`frontend/src/store/index.js` 是前端状态管理文件。

## 核心功能

### 用户登录注册

系统提供基础登录和注册功能。默认管理员账号为：

```text
admin / admin123
```

用户信息保存在 SQLite 数据库中。

### 图片检测

用户上传图片后，后端保存原图，调用 YOLOv8 模型进行目标检测，提取检测类别、置信度和边界框坐标，并使用 OpenCV 在图片上绘制检测框。检测结果保存到 `static/` 目录，同时检测记录写入数据库。

### 视频检测

用户上传视频后，后端使用 OpenCV 读取视频帧。为了提高性能，系统按固定间隔抽帧检测，并将检测框在后续若干帧中保持显示，最后输出带检测框的视频结果。

### 摄像头实时检测

前端通过浏览器摄像头获取实时画面，将当前帧转为 base64 图片发送给后端。后端对单帧进行 YOLO 检测并返回检测框信息，前端在视频画面上叠加显示检测框。摄像头检测不会保存用户画面，也不会写入历史记录。

### 历史记录管理

系统会保存图片和视频检测历史。用户可以查看检测时间、检测类型、原始文件、检测结果、最高置信度，并支持查看详情、下载结果、删除单条记录、批量删除和清空历史记录。

### 模型管理

系统支持查看当前模型、上传自定义模型、加载模型和删除模型。默认模型为 `yolov8n.pt`。

### AI 智能分析增强

系统在 YOLO 原始检测结果基础上增加了 AI 分析能力，包括：

- 单次图片检测智能分析
- 视频检测智能分析
- 历史记录智能分析
- DeepSeek 自然语言检测报告
- 基于检测结果的智能问答
- 大模型失败时的本地兜底报告

## 启动方式

后端推荐直接运行 `app.py`，不要使用 `python -m flask run`，因为项目中端口和初始化逻辑写在 `app.py` 的主入口里。

```bash
conda activate web_yolo
cd /Users/linky/Desktop/lin/study/实习/web_yolo_recong
python app.py
```

后端默认地址：

```text
http://localhost:5001
```

前端启动：

```bash
cd /Users/linky/Desktop/lin/study/实习/web_yolo_recong/frontend
npm run serve
```

前端默认地址：

```text
http://localhost:8080
```

## DeepSeek API 配置

大模型功能通过环境变量读取 API Key，避免将密钥写入代码。

终端启动时：

```bash
export DEEPSEEK_API_KEY="你的DeepSeek API Key"
python app.py
```

PyCharm 中可以在运行配置的 Environment variables 中添加：

```text
DEEPSEEK_API_KEY=你的DeepSeek API Key
```

默认使用模型：

```text
deepseek-v4-flash
```

## 答辩展示建议

推荐展示顺序：

1. 登录系统
2. 上传图片并查看检测结果
3. 展示智能分析面板
4. 点击生成 AI 报告
5. 打开智能问答，询问“这次检测结果可靠吗”
6. 上传短视频并展示视频分析
7. 打开历史记录页面，展示历史智能分析

这样可以完整体现项目从目标检测到智能分析再到大模型增强的闭环。
