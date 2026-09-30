from types import SimpleNamespace

from tagbot import agent
from tagbot.config import MAX_TOOL_ROUNDS
from tests.helpers import fake_msg


def call_item(name="get_message", args='{"message_id": "5"}', call_id="c1"):
    return SimpleNamespace(type="function_call", name=name, arguments=args, call_id=call_id)


def text_response(text):
    return SimpleNamespace(output=[SimpleNamespace(type="message")], output_text=text)


class FakeResponses:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.responses.pop(0)


class FakeChannel:
    def __init__(self):
        self.fetched = []

    async def fetch_message(self, message_id):
        self.fetched.append(message_id)
        return fake_msg(id=message_id, name="bob", content="original question")


def make_client(responses):
    return SimpleNamespace(responses=FakeResponses(responses))


async def test_runs_tool_then_returns_text():
    client = make_client([
        SimpleNamespace(output=[call_item()], output_text=""),
        text_response("summary!"),
    ])
    channel = FakeChannel()
    result = await agent.summarize(client, "gpt-6-luna", channel, [fake_msg(reply_to=5)])

    assert result == "summary!"
    assert channel.fetched == [5]
    second_input = client.responses.calls[1]["input"]
    outputs = [i for i in second_input if isinstance(i, dict) and i.get("type") == "function_call_output"]
    assert outputs[0]["call_id"] == "c1"
    assert "original question" in outputs[0]["output"]


async def test_forces_final_answer_after_max_rounds():
    looping = [SimpleNamespace(output=[call_item()], output_text="") for _ in range(MAX_TOOL_ROUNDS)]
    client = make_client(looping + [text_response("final")])
    result = await agent.summarize(client, "m", FakeChannel(), [fake_msg()])

    assert result == "final"
    calls = client.responses.calls
    assert len(calls) == MAX_TOOL_ROUNDS + 1
    assert all(c["tool_choice"] == "auto" for c in calls[:-1])
    assert calls[-1]["tool_choice"] == "none"


async def test_tool_errors_do_not_raise():
    client = make_client([
        SimpleNamespace(output=[call_item(name="nope", args="{}")], output_text=""),
        text_response("ok"),
    ])
    assert await agent.summarize(client, "m", FakeChannel(), [fake_msg()]) == "ok"
    out = client.responses.calls[1]["input"][-1]["output"]
    assert out.startswith("error: unknown tool")


async def test_empty_messages():
    client = make_client([])
    assert await agent.summarize(client, "m", FakeChannel(), []) == "No messages to summarize."
