import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app as backend


class DetectionOptionsTest(unittest.TestCase):
    def test_scene_defaults_and_explicit_threshold(self):
        for model, expected in [('models/pest_yolov8.pt', 0.05), ('models/yolov8n.pt', 0.25)]:
            with patch.object(backend, 'current_model_path', model):
                with backend.app.test_request_context('/api/detect_image', method='POST'):
                    self.assertEqual(backend.get_detection_confidence(), expected)
                with backend.app.test_request_context('/api/process_frame', json={'confidence': 0.37}):
                    self.assertEqual(backend.get_detection_confidence(), 0.37)

    def test_multipart_threshold(self):
        with backend.app.test_request_context('/api/detect_image', method='POST', data={'confidence': '0.15'}):
            self.assertEqual(backend.get_detection_confidence(), 0.15)

    def test_invalid_thresholds_are_rejected_before_inference(self):
        with backend.app.test_client() as client:
            for value in ['bad', 'nan', 'inf', -0.1, 0, 1, None, []]:
                response = client.post('/api/process_frame', json={'confidence': value})
                self.assertEqual(response.status_code, 400, value)
                self.assertFalse(response.json['success'])

    def test_model_change_is_rejected(self):
        with patch.object(backend, 'current_model_path', 'models/fire_yolov8.pt'):
            with backend.app.test_client() as client:
                for url in ['/api/detect_image', '/api/detect_video', '/api/process_frame']:
                    response = client.post(url, json={'model_path': 'models/pest_yolov8.pt'})
                    self.assertEqual(response.status_code, 409)

    def test_result_records_effective_parameters(self):
        @backend.guard_detection_request
        def predict():
            return backend.jsonify(success=True, detections=[])
        with backend.app.test_request_context('/api/process_frame', json={'confidence': 0.1}):
            response = predict()
            self.assertEqual(response.json['confidence_threshold'], 0.1)
            self.assertEqual(response.json['model_path'], backend.current_model_path)


if __name__ == '__main__':
    unittest.main()
