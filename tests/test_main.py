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
  assert len(documents) == 1
  assert documents[0].id == 1
  filter = oso.list_local(bob, "read", "Document", "document.id")
  documents = session.query(Document).filter(text(filter)).all()
  assert len(documents) == 1
  assert documents[0].id == 2

def test_library(oso_session: sqlalchemy_oso_cloud.Session, alice: Value):
  documents = oso_session.query(Document).authorized_for(alice, "read").all()
  assert len(documents) == 2
  assert documents[0].id == 1
  assert documents[1].id == 2 # alice can see this because it is "published"

def test_local_authorization_config_snapshot(snapshot):
  config = sqlalchemy_oso_cloud.oso.generate_local_authorization_config(Base.registry)
  snapshot.assert_match(yaml.dump(config))
