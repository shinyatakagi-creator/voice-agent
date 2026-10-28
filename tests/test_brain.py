from app.brain import get_ticket_status

def test_known_ticket():
    assert get_ticket_status("1042")["found"] is True

def test_unknown_ticket():
    assert get_ticket_status("9999")["found"] is False
