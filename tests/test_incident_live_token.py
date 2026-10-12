from pathlib import Path

DOC = Path(__file__).resolve().parents[1] / "deploy" / "INCIDENT-LIVE-TOKEN.md"


def test_incident_doc_lives_in_deploy() -> None:
    text = DOC.read_text()
    assert DOC.parent.name == "deploy"
    assert "TINKOFF_LIVE=0" in text
    assert "POST /kill" in text
    assert "отозвать" in text.lower()
    assert "не коммитить" in text.lower() or "Не коммитить" in text
