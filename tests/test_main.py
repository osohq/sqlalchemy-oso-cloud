from oso_cloud import Oso, Value
from sqlalchemy import text
from sqlalchemy.orm import Session
from .models import Document

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
  documents = oso_session.query(Document).authorized(alice, "read").all()
  assert len(documents) == 1
  assert documents[0].id == 1

def test_bob_can_read_different_document(oso_session: sqlalchemy_oso_cloud.Session, bob: Value):
  documents = oso_session.query(Document).authorized(bob, "read").all()
  assert len(documents) == 1
  assert documents[0].id == 2

def test_bob_cannot_eat_documents(oso_session: sqlalchemy_oso_cloud.Session, bob: Value):
  documents = oso_session.query(Document).authorized(bob, "eat").all()
  assert len(documents) == 0

def test_authorize_with_filter(oso_session: sqlalchemy_oso_cloud.Session, alice: Value):
  documents = (
      oso_session.query(Document)
      .filter(Document.id == 1)
      .authorized(alice, "read")
      .filter(Document.content == "hello")
      .all()
  )
  assert len(documents) == 1
  assert documents[0].id == 1

def test_authorize_doesnt_bring_in_filtered(oso_session: sqlalchemy_oso_cloud.Session, alice: Value):
  documents = (
      oso_session.query(Document)
      .filter(Document.content == "world")
      .authorized(alice, "read")
      .all()
  )
  assert len(documents) == 0
