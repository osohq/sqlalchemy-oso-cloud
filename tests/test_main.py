from oso_cloud import Oso, Value
from sqlalchemy import text
from sqlalchemy.orm import Session
from .models import Document, Base
import yaml

import sqlalchemy_oso_cloud

# This is the part our goal is to make nicer
def test_manual(oso: Oso, session: Session, alice: Value, bob: Value):
  filter = oso.list_local(alice, "read", "Document", "document.id")
  documents = session.query(Document).filter(text(filter)).all()
  assert len(documents) == 3
  assert any(document.id == 1 for document in documents)
  assert any(document.id == 2 for document in documents) # alice can see this because it is "published"
  assert any(document.id == 3 for document in documents) # alice can see this because it is "public"
  filter = oso.list_local(bob, "read", "Document", "document.id")
  documents = session.query(Document).filter(text(filter)).all()
  assert len(documents) == 2
  assert any(document.id == 2 for document in documents)
  assert any(document.id == 3 for document in documents) # bob can see this because it is "public"

def test_library(oso_session: sqlalchemy_oso_cloud.Session, alice: Value, bob: Value):
  documents = oso_session.query(Document).authorized_for(alice, "read").all()
  assert len(documents) == 3
  assert any(document.id == 1 for document in documents)
  assert any(document.id == 2 for document in documents) # alice can see this because it is "published"
  assert any(document.id == 3 for document in documents) # alice can see this because it is "public"
  documents = oso_session.query(Document).authorized_for(bob, "read").all()
  assert len(documents) == 2
  assert any(document.id == 2 for document in documents)
  assert any(document.id == 3 for document in documents) # bob can see this because it is "public"

def test_local_authorization_config_snapshot(snapshot):
  config = sqlalchemy_oso_cloud.oso.generate_local_authorization_config(Base.registry)
  snapshot.assert_match(yaml.dump(config))
