import axios from 'axios'
export const scenes = [
  {
    value: 'general',
    label: '通用检测',
    short: '通用',
    icon: 'Aim',
    color: '#19684b',
    file: 'general_yolov8s.pt',
    keywords: ['general', 'common', '通用'],
  },
  {
    value: 'drone',
    label: '无人机检测',
    short: '无人机',
    icon: 'Position',
    color: '#427d9b',
    file: 'drone_yolov8.pt',
    keywords: ['drone', 'uav', '无人机', '飞行器'],
  },
  {
    value: 'fire',
    label: '火灾检测',
    short: '火灾',
    icon: 'Warning',
    color: '#c87548',
    file: 'fire_yolov8.pt',
    keywords: ['fire', 'flame', 'smoke', '火灾', '火焰', '烟雾'],
  },
  {
    value: 'flower',
    label: '花卉检测',
    short: '花卉',
    icon: 'Cherry',
    color: '#b27386',
    file: 'flower_yolov8.pt',
    keywords: ['flower', 'rose', 'sunflower', 'tulip', 'daisy', '花卉', '花朵'],
  },
  {
    value: 'pest',
    label: '病虫害检测',
    short: '病虫害',
    icon: 'Grape',
    color: '#84954a',
    file: 'pest_yolov8.pt',
    keywords: ['pest', 'disease', 'leaf', 'plant', '病虫害', '病害', '虫害', '叶片'],
  },
]
export function modelScenes(model) {
  const text = `${model.name || ''} ${model.path || ''}`.toLowerCase()
  return scenes.filter(
    (scene) =>
      (scene.value === 'general' && model.path === 'models/yolov8n.pt') ||
      scene.keywords.some((keyword) => text.includes(keyword))
  )
}
export async function api(path, options = {}) {
  try {
    const response = await axios({ url: `/api${path}`, timeout: 90000, ...options })
    if (!response.data?.success) throw new Error(response.data?.message || '请求未完成')
    return response.data
  } catch (error) {
    throw new Error(
      error.response?.data?.message ||
        (error.code === 'ECONNABORTED'
          ? '请求超时，请稍后重试'
          : error.message === 'Network Error'
          ? '无法连接服务，请检查后端是否启动'
          : error.message)
    )
  }
}
export const percent = (value) => `${(Number(value || 0) * 100).toFixed(1)}%`
export const fileName = (path) =>
  String(path || '')
    .split(/[\\/]/)
    .pop() || '未加载'
export const typeLabel = (type) =>
  ({ image: '图片', video: '视频', camera: '摄像头' }[type] || type)
export function formatTime(value) {
  if (!value) return '--'
  const date = new Date(/[zZ]|[+-]\d\d:\d\d$/.test(value) ? value : `${value}Z`)
  return Number.isNaN(date.getTime()) ? '--' : date.toLocaleString('zh-CN', { hour12: false })
}
export function saveFile(content, name, type = 'application/json') {
  const url = URL.createObjectURL(new Blob([content], { type }))
  const link = document.createElement('a')
  link.href = url
  link.download = name
  link.hidden = true
  document.body.appendChild(link)
  link.click()
  link.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
export function exportRecords(records) {
  const escape = (value) => {
    let text = String(value ?? '')
    if (/^[=+@\-\t\r]/.test(text)) text = `'${text}`
    return `"${text.replace(/"/g, '""')}"`
  }
  const rows = [
    ['记录ID', '检测类型', '原始文件', '检测时间', '目标次数', '最高置信度'],
    ...records.map((r) => [
      r.id,
      typeLabel(r.detection_type),
      r.original_file || '',
      formatTime(r.created_at),
      r.detections?.length || 0,
      percent(r.confidence),
    ]),
  ]
  saveFile(
    '\ufeff' + rows.map((row) => row.map(escape).join(',')).join('\r\n'),
    'detection-history.csv',
    'text/csv;charset=utf-8'
  )
}
