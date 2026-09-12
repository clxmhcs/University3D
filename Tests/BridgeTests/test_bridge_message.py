import json

def test_stage_a_focus_message():
    message = {
        "protocolVersion": 1,
        "type": "focusObject",
        "objectID": "TEST-01",
    }
    encoded = json.dumps(message)
    decoded = json.loads(encoded)
    assert decoded["protocolVersion"] == 1
    assert decoded["type"] == "focusObject"
    assert decoded["objectID"] == "TEST-01"
