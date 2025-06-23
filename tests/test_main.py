from oso_cloud import Oso, Value
from sqlalchemy import text
from sqlalchemy.orm import Session
from .models import Document

# This is the part our goal is to make nicer
def test_alice_and_bob(oso: Oso, session: Session):
  filter = oso.list_local(Value("User", "alice"), "read", "Document", "document.id")
  documents = session.query(Document).filter(text(filter)).all()
  assert len(documents) == 1
  assert documents[0].id == 1

