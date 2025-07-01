from oso_cloud import Oso, Value
from sqlalchemy import text, func
from sqlalchemy.orm import Session, joinedload
from .models import Document, Base, Organization
import yaml
import pytest

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
  documents = oso_session.query(Document).authorized(alice, "read").all()
  assert len(documents) == 3
  assert any(document.id == 1 for document in documents)
  assert any(document.id == 2 for document in documents) # alice can see this because it is "published"
  assert any(document.id == 3 for document in documents) # alice can see this because it is "public"
  documents = oso_session.query(Document).authorized(bob, "read").all()
  assert len(documents) == 2
  assert any(document.id == 2 for document in documents)
  assert any(document.id == 3 for document in documents) # bob can see this because it is "public"

def test_local_authorization_config_snapshot(snapshot):
  config = sqlalchemy_oso_cloud.oso.generate_local_authorization_config(Base.registry)
  snapshot.assert_match(yaml.dump(config))

def test_bob_can_read_different_document(oso_session: sqlalchemy_oso_cloud.Session, bob: Value):
  documents = oso_session.query(Document).authorized(bob, "read").all()
  assert len(documents) == 2
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

def test_authorize_doesnt_bring_in_filtered(oso_session: sqlalchemy_oso_cloud.Session, bob: Value):
  documents = (
      oso_session.query(Document)
      .filter(Document.id == 1)
      .authorized(bob, "read")
      .all()
  )
  assert len(documents) == 0

# In current implementation: chaining .authorized produces an AND intersection of the results
def test_authorize_chaining(oso_session: sqlalchemy_oso_cloud.Session, alice: Value, bob: Value):
  documents = (
      oso_session.query(Document)
      .authorized(alice, "read")
      .authorized(bob, "read")
      .all()
  )
  assert len(documents) > 1

def test_multimodel_authorize_raises_error(oso_session: sqlalchemy_oso_cloud.Session, alice: Value):
  with pytest.raises(ValueError):
    _documents = oso_session.query(Document, Organization).authorized(alice, "read")

  # multi-model queries still work without authorization
  # (this is a limitation of the current implementation)
  documents_and_organizations = (
      oso_session.query(Document, Organization)
      .join(Organization)
      .all()
  )

  first_result = documents_and_organizations[0]
  assert len(first_result) == 2
    
  document, organization = first_result
  assert isinstance(document, Document)
  assert isinstance(organization, Organization)


def test_common_clauses(oso_session: sqlalchemy_oso_cloud.Session, alice: Value):
  documents = (
      oso_session.query(Document)
      .authorized(alice, "read")
      .filter(Document.id == 1)
      .order_by(Document.id)
      .limit(10)
      .all()
  )
  assert len(documents) > 0

def test_authorize_with_relationship_clauses(oso_session: sqlalchemy_oso_cloud.Session, alice: Value):
  documents = (
      oso_session.query(Document)
      .authorized(alice, "read")
      .join(Organization)
      .all()
  )
  assert len(documents) > 0

  documents = (
      oso_session.query(Document)
      .authorized(alice, "read")
      .options(joinedload(Document.organization))
      .all()
  )

  assert len(documents) > 0

  documents = (
      oso_session.query(Document)
      .authorized(alice, "read")
      .join(Organization)
      .filter(Organization.name == "acme")
      .all()
  )
  assert len(documents) > 0

def test_authorized_with_complex_queries(oso_session: sqlalchemy_oso_cloud.Session, alice: Value):
  documents = (
      oso_session.query(Document)
      .authorized(alice, "read")
      .filter(
          Document.id.in_(
              oso_session.query(Document.id).filter(Document.is_public == True)
          )
      )
      .all()
  )
  assert len(documents) > 0
  assert all(document.is_public for document in documents)  # All returned documents should be public

  count = oso_session.query(func.count(Document.id)).group_by(Document.status).authorized(alice, "read").all()
  assert len(count) > 0 
