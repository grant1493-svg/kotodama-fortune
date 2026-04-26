import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from unittest.mock import patch, MagicMock
import line_tasks


class TestParseLineLog(unittest.TestCase):

    SAMPLE_LOG = """[LINE] "業務グループ"のトーク履歴

保存日時：2026年4月26日 10:00

2026/04/20(月) 10:32\t田中\t見積書って今週中に出せますか？
2026/04/20(月) 10:35\t課長\tはい、木曜までに営業部へ提出してください
2026/04/20(月) 10:40\t田中\tわかりました
2026/04/20(月) 10:45\t田中\t[スタンプ]
2026/04/20(月) 11:00\t鈴木\t倉庫の在庫チェックをお願いします
"""

    def test_returns_messages_list(self):
        result = line_tasks.parse_line_log(self.SAMPLE_LOG)
        self.assertIn("messages", result)
        self.assertIsInstance(result["messages"], list)

    def test_filters_stamps(self):
        result = line_tasks.parse_line_log(self.SAMPLE_LOG)
        texts = [m["text"] for m in result["messages"]]
        self.assertNotIn("[スタンプ]", texts)

    def test_parses_sender_and_text(self):
        result = line_tasks.parse_line_log(self.SAMPLE_LOG)
        first = result["messages"][0]
        self.assertEqual(first["sender"], "田中")
        self.assertEqual(first["text"], "見積書って今週中に出せますか？")
        self.assertEqual(first["datetime"], "2026/04/20(月) 10:32")

    def test_extracts_date_range(self):
        result = line_tasks.parse_line_log(self.SAMPLE_LOG)
        self.assertEqual(result["start_date"], "2026/04/20")
        self.assertEqual(result["end_date"], "2026/04/20")

    def test_message_count(self):
        result = line_tasks.parse_line_log(self.SAMPLE_LOG)
        self.assertEqual(len(result["messages"]), 4)  # スタンプ除外後
