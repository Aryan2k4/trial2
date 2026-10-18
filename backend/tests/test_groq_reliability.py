from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from app.services.ai_providers.groq_provider import GroqProvider


def provider_with_responses(*responses):
    provider = GroqProvider.__new__(GroqProvider)
    provider.model = 'test-model'
    provider._models_to_try = ['test-model', 'backup-model']
    provider.client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=Mock(side_effect=responses))))
    return provider


def response(content='Finished', calls=None):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content, tool_calls=calls))])


def test_stream_does_not_pay_for_a_second_copy_of_completed_summary():
    provider = provider_with_responses(response())
    events = list(provider.run_agentic_task_stream('system', 'task', []))
    assert events[-1]['type'] == 'done'
    assert events[-1]['final_text'] == 'Finished'
    assert provider.client.chat.completions.create.call_count == 1


def test_auth_or_quota_failure_does_not_cycle_through_models():
    error = RuntimeError('quota exhausted')
    error.status_code = 429
    provider = provider_with_responses(error, response())
    with pytest.raises(RuntimeError):
        provider.generate('system', 'task')
    assert provider.client.chat.completions.create.call_count == 1


def test_brief_rate_limit_wait_retries_only_the_request(monkeypatch):
    error = RuntimeError('brief quota cooldown')
    error.status_code = 429
    error.response = SimpleNamespace(headers={'retry-after': '2'})
    provider = provider_with_responses(error, response())
    sleep = Mock()
    monkeypatch.setattr('time.sleep', sleep)
    assert provider.generate('system', 'task') == 'Finished'
    sleep.assert_called_once_with(2.0)
    assert provider.client.chat.completions.create.call_count == 2


def test_interrupted_real_stream_never_replays_mutating_mock_tools(monkeypatch):
    from app.core import intelligence_engine as engine
    class Interrupted:
        def run_agentic_task_stream(self, *args):
            yield {'type': 'tool_call', 'tool': 'create_work_order', 'args': {}, 'result': {'id': 1}}
            raise RuntimeError('provider interrupted')
    monkeypatch.setattr(engine, 'get_ai_provider', lambda: (Interrupted(), 'groq'))
    fallback = Mock(side_effect=AssertionError('Must not replay tools'))
    monkeypatch.setattr(engine.MockProvider, 'run_agentic_task_stream', fallback)
    events = list(engine._run_investigation_stream('energy', 'HQ', None, 'system', 'task', []))
    assert events[-1]['type'] == 'error'
    fallback.assert_not_called()
