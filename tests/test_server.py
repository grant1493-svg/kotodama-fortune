import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
import json
from unittest.mock import patch, MagicMock
import server


class TestUploadEndpoint(unittest.TestCase):

    def setUp(self):
        server.app.config["TESTING"] = True
        self.client = server.app.test_client()

    def _make_sample_txt(self):
        content = (
            "[LINE] \"テストグループ\"のトーク履歴\n\n"
            "保存日時：2026年4月26日 10:00\n\n"
            "2026/04/20(月) 10:32\t田中\t見積書を提出してください\n"
            "2026/04/20(月) 10:35\t課長\t木曜までにお願いします\n"
        )
        return content.encode("utf-8")

    def test_no_file_returns_400(self):
        resp = self.client.post("/upload")
        self.assertEqual(resp.status_code, 400)
        data = json.loads(resp.data)
        self.assertIn("error", data)

    def test_non_txt_file_returns_400(self):
        from io import BytesIO
        resp = self.client.post(
            "/upload",
            data={"file": (BytesIO(b"dummy"), "log.pdf")},
            content_type="multipart/form-data"
        )
        self.assertEqual(resp.status_code, 400)
        data = json.loads(resp.data)
        self.assertIn("error", data)

    def test_valid_txt_calls_pipeline_and_returns_html(self):
        from io import BytesIO
        mock_tasks = [{
            "content": "見積書を提出する", "assignee": "田中",
            "deadline": "4/28", "priority": "高",
            "speaker": "課長", "datetime": "2026/04/20(月) 10:35"
        }]
        with patch("server.line_tasks.extract_tasks_via_api", return_value=mock_tasks):
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test-dummy"}):
                resp = self.client.post(
                    "/upload",
                    data={"file": (BytesIO(self._make_sample_txt()), "log.txt")},
                    content_type="multipart/form-data"
                )
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode("utf-8")
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("見積書を提出する", html)

    def test_missing_api_key_returns_500(self):
        from io import BytesIO
        env_backup = os.environ.copy()
        os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            resp = self.client.post(
                "/upload",
                data={"file": (BytesIO(self._make_sample_txt()), "log.txt")},
                content_type="multipart/form-data"
            )
        finally:
            os.environ.update(env_backup)
        self.assertEqual(resp.status_code, 500)
        data = json.loads(resp.data)
        self.assertIn("error", data)
