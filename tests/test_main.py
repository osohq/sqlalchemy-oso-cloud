from oso_cloud import Oso, Value
from sqlalchemy import text
from sqlalchemy.orm import Session
from .models import Document

import sqlalchemy_oso_cloud
from sqlalchemy_oso_cloud import select

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
  assert len(documents) == 1
  assert documents[0].id == 1

def test_bob_can_read_different_document(oso_session: sqlalchemy_oso_cloud.Session, bob: Value):
  documents = oso_session.query(Document).authorized_for(bob, "read").all()
  assert len(documents) == 1
  assert documents[0].id == 2

def test_bob_cannot_eat_documents(oso_session: sqlalchemy_oso_cloud.Session, bob: Value):
  documents = oso_session.query(Document).authorized_for(bob, "eat").all()
  assert len(documents) == 0

def test_select_alice_can_read(oso_session: sqlalchemy_oso_cloud.Session, alice: Value):
  statement = select(Document).authorized_for(alice, "read")
  documents = oso_session.execute(statement).scalars().all()
  assert len(documents) == 1
  assert documents[0].id == 1

def test_select_bob_can_read_different_document(oso_session: sqlalchemy_oso_cloud.Session, bob: Value):
  statement = select(Document).authorized_for(bob, "read")
  documents = oso_session.execute(statement).scalars().all()
  assert len(documents) == 1
  assert documents[0].id == 2

def test_select_bob_cannot_eat_document(oso_session: sqlalchemy_oso_cloud.Session, bob: Value):
  statement = select(Document).authorized_for(bob, "eat")
  documents = oso_session.execute(statement).scalars().all()
  assert len(documents) == 0

def test_select_select_with_where(oso_session: sqlalchemy_oso_cloud.Session, bob: Value):
  statement = select(Document).where(Document.id == 2).authorized_for(bob, "read").where(Document.content == "world")
  documents = oso_session.execute(statement).scalars().all()
  assert len(documents) == 1
  assert documents[0].id == 2

def test_select_without_auth_filter(oso_session: sqlalchemy_oso_cloud.Session):
  # This should return all documents since we are not filtering by authorization
  statement = select(Document)
  documents = oso_session.execute(statement).scalars().all()
  assert len(documents) == 2
  assert documents[0].id == 1
  assert documents[1].id == 2
  