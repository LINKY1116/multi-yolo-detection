# AI开发B工作说明与代码掌握指南

## 你的负责模块

你的方向是 AI 开发 B：AI 检测结果分析增强模块。

该模块不是训练模型，而是对 YOLO 模型输出结果进行二次分析、统计、判断和解释，并进一步接入 DeepSeek 大模型，实现自然语言报告和智能问答。

你的功能链路是：

```text
YOLO原始检测结果
→ 结构化统计分析
→ 复核规则判断
→ 图片/视频智能分析展示
→ 历史记录智能分析
→ 大模型自然语言报告
→ 检测结果智能问答
```

## 你新增和改进的功能

### 1. 图片检测智能分析

图片检测完成后，系统不只返回检测框，还会生成 `analysis` 分析结果。

分析指标包括：

- 目标总数
- 类别分布
- 主要类别
- 平均置信度
- 最高置信度
- 低置信度目标数量
- 低置信度比例
- 是否建议人工复核
- 自然语言分析结论

### 2. 视频检测智能分析

视频检测完成后，系统会基于视频检测结果生成视频维度分析。

新增指标包括：

- 处理帧数
- 视频总帧数
- 检测间隔
- 采样帧数
- 有目标帧数
- 有目标帧比例
- 平均目标/采样帧
- 视频检测分析结论

### 3. 历史记录智能分析

系统会统计用户全部历史检测记录，形成长期检测分析。

分析指标包括：

- 历史检测次数
- 图片/视频/摄像头检测次数
- 累计目标数
- 历史平均置信度
- 历史最高置信度
- 低置信度记录数
- 空结果记录数
- 常见类别
- 最近检测时间
- 是否建议复核

### 4. AI自然语言报告

用户点击“生成AI报告”后，后端会将当前检测统计结果整理成上下文，调用 DeepSeek 快速模型生成中文检测报告。

报告内容包括：

- 检测概况
- 主要目标
- 可信度判断
- 复核建议

### 5. 检测结果智能问答

用户点击“智能问答”后，可以在弹窗中围绕当前检测结果提问。

例如：

```text
这次检测结果可靠吗？
为什么建议复核？
检测到了哪些主要目标？
这个视频检测结果说明了什么？
```

后端会结合当前检测结果、统计分析和对话历史调用 DeepSeek 返回回答。

### 6. 大模型失败兜底

如果 DeepSeek API Key 没有配置、网络失败或接口异常，系统不会崩溃，而是返回本地基础报告。

这是答辩时的加分点：

```text
大模型是增强能力，核心统计分析能力不依赖外部 API。
```

## 后端代码位置

### `analyze_detections`

位置：

[app.py](/Users/linky/Desktop/lin/study/实习/web_yolo_recong/app.py:112)

作用：

对单次 YOLO 检测结果进行结构化统计。

你要掌握：

```python
low_confidence_threshold = 0.6
```

含义：低于 60% 的目标视为低置信度目标。

核心判断：

```python
review_required = (
    total_objects == 0 or
    avg_confidence < low_confidence_threshold or
    low_confidence_ratio > 0.3
)
```

含义：

- 没有检测到目标
- 平均置信度低于 60%
- 低置信度目标比例超过 30%

满足以上任一情况，就建议人工复核。

### `analyze_video_detections`

位置：

[app.py](/Users/linky/Desktop/lin/study/实习/web_yolo_recong/app.py:162)

作用：

对视频检测结果进行分析。

你要掌握：

```python
sampled_frame_count
detected_frame_count
detected_frame_ratio
avg_detections_per_sampled_frame
```

含义：

- `sampled_frame_count`：实际参与检测的采样帧数量
- `detected_frame_count`：检测到目标的帧数量
- `detected_frame_ratio`：有目标帧占采样帧的比例
- `avg_detections_per_sampled_frame`：平均每个采样帧检测到多少目标

答辩说法：

```text
视频逐帧检测计算量较大，因此系统采用间隔抽帧检测。我在此基础上统计采样帧、有目标帧和平均目标数量，用于衡量视频检测结果的稳定性。
```

### `analyze_history_records`

位置：

[app.py](/Users/linky/Desktop/lin/study/实习/web_yolo_recong/app.py:199)

作用：

分析用户所有历史检测记录。

你要掌握：

```text
这个函数不是分析单次检测，而是分析用户长期检测数据。
```

它会从数据库记录里读取：

```python
DetectionResult
```

并统计检测类型、置信度、类别分布和低质量记录。

### `summarize_detection_context`

位置：

[app.py](/Users/linky/Desktop/lin/study/实习/web_yolo_recong/app.py:309)

作用：

压缩发送给大模型的检测上下文。

你要掌握：

```text
不是把所有检测框都发给大模型，而是发送统计结果和置信度最高的前 8 个检测样本。
```

这样做的原因：

- 减少 token 消耗
- 提升响应速度
- 让大模型更关注重点目标
- 避免检测结果过多导致上下文冗余

### `build_local_report`

位置：

[app.py](/Users/linky/Desktop/lin/study/实习/web_yolo_recong/app.py:332)

作用：

大模型不可用时生成本地基础报告。

答辩说法：

```text
为了保证系统稳定性，我设计了本地兜底逻辑。即使大模型接口失败，用户仍然能看到基于本地统计结果的基础分析报告。
```

### `call_deepseek`

位置：

[app.py](/Users/linky/Desktop/lin/study/实习/web_yolo_recong/app.py:349)

作用：

调用 DeepSeek 大模型接口。

你要掌握：

```text
DeepSeek 使用 OpenAI 兼容接口。
请求地址是 https://api.deepseek.com/chat/completions。
模型默认 deepseek-v4-flash。
API Key 优先使用前端请求传入的 api_key。
如果前端没有传入，则读取后端环境变量 DEEPSEEK_API_KEY 作为备用。
```

重点：

```python
api_key = api_key or os.getenv('DEEPSEEK_API_KEY')
```

答辩说法：

```text
API Key 属于敏感信息，所以没有写死在代码里。系统支持用户在页面首次使用 AI 功能时临时输入，前端保存到 sessionStorage 中，关闭浏览器后失效；后端也保留环境变量作为备用方式。
```

### `/api/detect_image`

位置：

[app.py](/Users/linky/Desktop/lin/study/实习/web_yolo_recong/app.py:270)

改动：

图片检测完成后调用：

```python
analysis = analyze_detections(detections, 'image')
```

并在返回结果中增加：

```python
'analysis': analysis
```

### `/api/detect_video`

位置：

[app.py](/Users/linky/Desktop/lin/study/实习/web_yolo_recong/app.py:593)

改动：

视频检测完成后调用：

```python
analysis = analyze_video_detections(...)
```

并在返回结果中增加：

```python
'analysis': analysis
```

### `/api/analysis/history/<user_id>`

位置：

[app.py](/Users/linky/Desktop/lin/study/实习/web_yolo_recong/app.py:685)

作用：

返回用户历史检测智能分析。

前端历史页会调用这个接口。

### `/api/analysis/report`

位置：

[app.py](/Users/linky/Desktop/lin/study/实习/web_yolo_recong/app.py:825)

作用：

生成自然语言 AI 检测报告。

前端点击“生成AI报告”时调用。

### `/api/analysis/chat`

位置：

[app.py](/Users/linky/Desktop/lin/study/实习/web_yolo_recong/app.py:873)

作用：

围绕当前检测结果进行智能问答。

前端智能问答弹窗发送问题时调用。

## 前端代码位置

### 智能分析面板

位置：

[Detection.vue](/Users/linky/Desktop/lin/study/实习/web_yolo_recong/frontend/src/views/Detection.vue:210)

展示内容：

- 目标总数
- 平均置信度
- 最高置信度
- 低置信度数量
- 是否建议复核
- 类别分布
- 分析结论

### 视频分析指标

位置：

[Detection.vue](/Users/linky/Desktop/lin/study/实习/web_yolo_recong/frontend/src/views/Detection.vue:250)

展示内容：

- 处理帧数
- 采样帧数
- 有目标帧数
- 平均目标/采样帧

### AI报告和智能问答按钮

位置：

[Detection.vue](/Users/linky/Desktop/lin/study/实习/web_yolo_recong/frontend/src/views/Detection.vue:254)

按钮：

```text
生成AI报告
智能问答
设置API Key
清除Key
```

其中“设置API Key”用于弹窗输入 DeepSeek Key，“清除Key”用于删除当前浏览器会话中保存的 key。

### 智能问答弹窗

位置：

[Detection.vue](/Users/linky/Desktop/lin/study/实习/web_yolo_recong/frontend/src/views/Detection.vue:444)

作用：

展示对话历史，输入用户问题，并发送到后端智能问答接口。

### `generateAiReport`

位置：

[Detection.vue](/Users/linky/Desktop/lin/study/实习/web_yolo_recong/frontend/src/views/Detection.vue:834)

作用：

调用：

```text
/api/analysis/report
```

成功后把报告保存到：

```javascript
aiReport
```

并展示在页面中。

### API Key 弹窗与会话保存

位置：

[Detection.vue](/Users/linky/Desktop/lin/study/实习/web_yolo_recong/frontend/src/views/Detection.vue:499)

作用：

用户第一次使用 AI 功能时，系统弹出对话框输入 DeepSeek API Key。

保存方式：

```javascript
sessionStorage.setItem('deepseek_api_key', apiKey)
```

读取方式：

```javascript
sessionStorage.getItem('deepseek_api_key')
```

清除方式：

```javascript
sessionStorage.removeItem('deepseek_api_key')
```

你要掌握：

```text
sessionStorage 只在当前浏览器会话有效，关闭浏览器后会失效，比写死在代码里更安全，也方便课程演示。
```

### `sendChatMessage`

位置：

[Detection.vue](/Users/linky/Desktop/lin/study/实习/web_yolo_recong/frontend/src/views/Detection.vue:887)

作用：

调用：

```text
/api/analysis/chat
```

发送内容包括：

- 用户问题
- 当前检测分析结果
- 当前检测目标列表
- 最近对话历史

### 历史智能分析面板

位置：

[History.vue](/Users/linky/Desktop/lin/study/实习/web_yolo_recong/frontend/src/views/History.vue:53)

展示内容：

- 历史检测次数
- 历史平均置信度
- 低置信度记录
- 累计目标数
- 检测类型分布
- 常见类别
- 历史分析结论

### `fetchHistoryAnalysis`

位置：

[History.vue](/Users/linky/Desktop/lin/study/实习/web_yolo_recong/frontend/src/views/History.vue:375)

作用：

调用：

```text
/api/analysis/history/<user_id>
```

获取历史智能分析结果。

## 老师可能问的问题

### 你的 AI 分析和 YOLO 检测有什么区别？

回答：

```text
YOLO 负责输出类别、置信度和坐标等原始检测结果。我负责对这些结果进行二次分析，包括类别分布统计、平均置信度计算、低置信度目标统计和复核建议判断。然后再结合大模型生成自然语言报告，让用户更容易理解检测结果。
```

### 为什么设置 0.6 作为低置信度阈值？

回答：

```text
0.6 是经验阈值，用来区分较可靠和需要复核的检测目标。低于 60% 的目标更容易出现误检，所以纳入低置信度统计。后续可以把这个阈值做成配置项，根据具体应用场景调整。
```

### 为什么低置信度比例超过 30% 就建议复核？

回答：

```text
如果一批检测结果中超过三成目标置信度偏低，说明整体检测质量不稳定，可能受到图片模糊、遮挡、目标过小或模型不适配影响，所以系统给出人工复核建议。
```

### 视频为什么不逐帧检测？

回答：

```text
逐帧检测计算量很大，处理速度会明显下降。系统采用间隔抽帧检测，提高视频处理效率。我在抽帧检测基础上统计采样帧数、有目标帧数和平均目标数量，用来评价视频检测结果。
```

### 大模型是不是只是套壳？

回答：

```text
不是。大模型只负责把结构化分析结果转成自然语言报告和问答回复。核心分析能力在本地完成，包括检测统计、复核判断、历史分析和上下文压缩。即使大模型不可用，系统也能生成基础分析报告。
```

### 为什么不把所有检测结果都发给大模型？

回答：

```text
检测结果可能很多，全部发送会增加 token 消耗、降低速度，也会让模型难以抓住重点。所以我只发送统计分析结果和置信度最高的部分样本，既节省资源，也更稳定。
```

### API Key 为什么不写在代码里？

回答：

```text
API Key 是敏感信息，写入代码容易泄露。因此系统没有硬编码密钥。用户首次使用 AI 功能时可以在页面弹窗中输入 key，前端只保存到当前浏览器会话的 sessionStorage 中；后端也支持从环境变量 DEEPSEEK_API_KEY 读取作为备用。
```

### 为什么用 sessionStorage 保存 API Key？

回答：

```text
sessionStorage 关闭浏览器后会失效，适合课程演示和本地使用。这样既避免把 API Key 写进源码或提交到 GitHub，也比每次都配置环境变量更方便。
```

### 大模型调用失败怎么办？

回答：

```text
后端做了异常处理和本地兜底报告。如果 DeepSeek 接口失败，系统不会崩溃，仍然会根据本地统计结果返回基础报告。
```

## 你需要熟悉的核心数据结构

### `detections`

YOLO 检测结果列表。

图片检测中的一项：

```json
{
  "class": "car",
  "confidence": 0.61,
  "bbox": [356, 403, 393, 447]
}
```

视频检测中的一项会多一个 `frame`：

```json
{
  "frame": 120,
  "class": "person",
  "confidence": 0.72,
  "bbox": [100, 80, 180, 260]
}
```

### `analysis`

智能分析结果。

```json
{
  "total_objects": 10,
  "class_counts": {"car": 10},
  "main_class": "car",
  "avg_confidence": 0.41,
  "max_confidence": 0.61,
  "low_confidence_count": 9,
  "review_required": true,
  "conclusion": "本次检测共发现 10 个目标，部分目标置信度偏低，建议人工复核检测结果。"
}
```

## 答辩时可以背的总结

```text
我负责的是 AI 检测结果智能分析增强模块。YOLO 模型输出的是类别、置信度、坐标和视频帧号等原始数据，我在后端设计了结构化分析函数，对目标数量、类别分布、平均置信度、低置信度比例等指标进行统计，并根据规则判断是否需要人工复核。对于视频检测，我增加了处理帧数、采样帧数、有目标帧数和平均目标数等视频维度指标。对于历史记录，我实现了用户长期检测数据分析。最后，我接入 DeepSeek 大模型，将结构化检测结果生成自然语言报告，并实现了围绕当前检测结果的智能问答功能。
```

## 你答辩前要会操作的演示流程

1. 启动后端 `python app.py`
2. 启动前端 `npm run serve`
3. 登录 `admin / admin123`
4. 上传图片检测
5. 讲解智能分析面板
6. 点击“生成AI报告”，首次使用时输入 DeepSeek API Key
7. 打开“智能问答”，输入“这次检测结果可靠吗”
8. 上传短视频检测，讲解视频分析指标
9. 打开检测历史，讲解历史智能分析

## 注意事项

摄像头检测不会保存图片或视频，也不会写入历史记录。它只是把当前帧临时发送给后端检测，后端返回检测框后前端实时显示。

DeepSeek API Key 不要提交到代码仓库，也不要写进文档或源码。演示时推荐通过页面弹窗临时输入；如果使用后端环境变量，也不要把环境变量写入代码文件。
