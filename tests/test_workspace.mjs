import test from 'node:test'
import assert from 'node:assert/strict'
import { exportRecords, modelScenes, saveFile } from '../frontend/src/lib/workspace.js'

test('models are classified by scene keywords and the default model path', () => {
  assert.deepEqual(
    modelScenes({ path: 'models/yolov8n.pt' }).map((s) => s.value),
    ['general']
  )
  assert.deepEqual(
    modelScenes({ name: '20261007_fire_yolov8.pt' }).map((s) => s.value),
    ['fire']
  )
  assert.deepEqual(
    modelScenes({ name: 'flower_yolov8.pt' }).map((s) => s.value),
    ['flower']
  )
  assert.deepEqual(modelScenes({ name: 'best.pt' }), [])
})

test('exports attach a download link and escape CSV content', async (t) => {
  let blob,
    link,
    attached = false,
    clicked = false
  t.mock.method(URL, 'createObjectURL', (value) => {
    blob = value
    return 'blob:test'
  })
  t.mock.method(URL, 'revokeObjectURL', () => {})
  t.mock.method(globalThis, 'setTimeout', (callback) => {
    callback()
    return 1
  })
  const originalDocument = globalThis.document
  globalThis.document = {
    body: {
      appendChild: (value) => {
        assert.equal(value, link)
        attached = true
      },
    },
    createElement: (tag) => {
      assert.equal(tag, 'a')
      link = {
        click: () => {
          assert.ok(attached)
          clicked = true
        },
        remove: () => {
          attached = false
        },
      }
      return link
    },
  }
  t.after(() => {
    if (originalDocument === undefined) delete globalThis.document
    else globalThis.document = originalDocument
  })

  saveFile('{"count":1}', 'detection.json')
  assert.equal(link.download, 'detection.json')
  assert.equal(await blob.text(), '{"count":1}')
  assert.ok(clicked)
  assert.equal(attached, false)

  exportRecords([
    {
      id: 1,
      detection_type: 'image',
      original_file: '=SUM(1,2)".jpg',
      created_at: '2026-10-07T00:00:00',
      detections: [{ class: 'car' }],
      confidence: 0.75,
    },
  ])
  assert.equal(link.download, 'detection-history.csv')
  assert.equal(blob.type, 'text/csv;charset=utf-8')
  const bytes = new Uint8Array(await blob.arrayBuffer())
  assert.deepEqual([...bytes.slice(0, 3)], [0xef, 0xbb, 0xbf])
  const csv = await blob.text()
  assert.ok(csv.includes('"\'=SUM(1,2)"".jpg"'))
  assert.ok(csv.includes('"75.0%"'))
  assert.equal(csv.split('\r\n').length, 2)
})
