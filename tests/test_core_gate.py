from agent_open_mind import taint_check, TAINT_PRINCIPLE


def test_absent_thought_tainted():
    r = taint_check({"agent": "07", "envelope_id": "e", "thought": "  ",
                     "result": "done"})
    assert r["tainted"] is True and "tainted" in r["reason"]


def test_present_thought_passes():
    r = taint_check({"thought": "checked the rubric first", "result": "ok"})
    assert r["tainted"] is False and r["reason"] is None


def test_principle_is_stated():
    assert "never silently admitted" in TAINT_PRINCIPLE
