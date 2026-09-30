from datetime import datetime, timezone
from types import SimpleNamespace


def fake_msg(id=1, name="alice", content="hi", reply_to=None, attachments=0, embeds=0):
    return SimpleNamespace(
        id=id,
        created_at=datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc),
        author=SimpleNamespace(display_name=name, id=100),
        content=content,
        reference=SimpleNamespace(message_id=reply_to) if reply_to else None,
        attachments=[object()] * attachments,
        embeds=[object()] * embeds,
    )
