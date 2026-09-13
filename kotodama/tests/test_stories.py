import os
import sys
from pathlib import Path
from unittest.mock import patch
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('FLASK_SECRET_KEY', 'test-secret')
from app import app
from stories import STORIES, recommend_story

@pytest.mark.parametrize('key', STORIES)
def test_shared_story_available_without_name_or_generation(key):
    with app.test_client() as client, patch('app.generate_fortune') as generate:
        response = client.get('/stories/' + key)
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert STORIES[key]['title'] in html
        assert '/static/stories/' + key + '.png' in html
        assert '個別に生成した鑑定ではありません' in html
        assert 'adsbygoogle' not in html
        assert 'textarea' in html and 'name="reflection"' not in html
        generate.assert_not_called()
        assert len(STORIES[key]['scenes']) == 4

def test_unknown_story_returns_404():
    with app.test_client() as client:
        assert client.get('/stories/unknown').status_code == 404

@pytest.mark.parametrize('message, expected', [('今日は休もう', 'rest'), ('新しい挑戦', 'step'), ('友達と話す', 'bridge'), (None, 'bridge')])
def test_message_hint_has_known_fallback(message, expected):
    assert recommend_story(message) == expected

@pytest.mark.parametrize('path', ['/register', '/name/さくら'])
def test_public_entry_links_to_story(path):
    with app.test_client() as client:
        assert '/stories/bridge' in client.get(path).get_data(as_text=True)
