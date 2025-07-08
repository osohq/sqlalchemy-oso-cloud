from oso_cloud import Oso, Value
from sqlalchemy import text, func, select as sqla_select
from sqlalchemy.orm import Session, joinedload
from .models import Document, Base, Organization
import yaml


import sqlalchemy_oso_cloud
from sqlalchemy_oso_cloud import select, authorized

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
  filter = oso.list_local(alice, "write", "Document", "document.id")
  documents = session.query(Document).filter(text(filter)).all()
  assert len(documents) == 2
  filter = oso.list_local(bob, "write", "Document", "document.id")
  documents = session.query(Document).filter(text(filter)).all()
  assert len(documents) == 1

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

def test_alice_and_bob_write(oso_session: sqlalchemy_oso_cloud.Session, alice: Value, bob: Value):
  documents = oso_session.query(Document).authorized(alice, "write").all()
  assert len(documents) == 2
  documents = oso_session.query(Document).authorized(bob, "write").all()
  assert len(documents) == 1

def test_bob_can_read_different_document(oso_session: sqlalchemy_oso_cloud.Session, bob: Value):
  documents = oso_session.query(Document).authorized(bob, "read").all()
  assert len(documents) == 2
  assert documents[0].id == 2

def test_bob_cannot_eat_documents(oso_session: sqlalchemy_oso_cloud.Session, bob: Value):
  documents = oso_session.query(Document).authorized(bob, "eat").all()
  assert len(documents) == 0

def test_select_alice_can_read(oso_session: sqlalchemy_oso_cloud.Session, alice: Value):
  statement = select(Document).authorized(alice, "read")
  documents = oso_session.execute(statement).scalars().all()
  assert len(documents) > 1
  assert documents[0].id == 1

def test_select_bob_can_read_different_document(oso_session: sqlalchemy_oso_cloud.Session, bob: Value):
  statement = select(Document).authorized(bob, "read")
  documents = oso_session.execute(statement).scalars().all()
  assert len(documents) > 1
  assert documents[0].id == 2

def test_select_bob_cannot_eat_document(oso_session: sqlalchemy_oso_cloud.Session, bob: Value):
  statement = select(Document).authorized(bob, "eat")
  documents = oso_session.execute(statement).scalars().all()
  assert len(documents) == 0

def test_select_select_with_where(oso_session: sqlalchemy_oso_cloud.Session, bob: Value):
  statement = select(Document).where(Document.id == 2).authorized(bob, "read").where(Document.content == "world")
  documents = oso_session.execute(statement).scalars().all()
  assert len(documents) == 1
  assert documents[0].id == 2

def test_select_without_auth_filter(oso_session: sqlalchemy_oso_cloud.Session):
  # This should return all documents since we are not filtering by authorization
  statement = select(Document)
  documents = oso_session.execute(statement).scalars().all()
  assert len(documents) > 2
  assert documents[0].id == 1
  assert documents[1].id == 2

def test_authorized_as_options(session, alice: Value):
  statement = sqla_select(Document).options(authorized(alice, "read", Document))
  documents = session.execute(statement).scalars().all()
  assert len(documents) > 0

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

def test_multimodel_authorize(oso_session: sqlalchemy_oso_cloud.Session, alice: Value):
  documents = (
    oso_session.query(Document, Organization)
    .join(Organization)
    .authorized(alice, "read")
    .all()
    )

  # 0 because Organization has no "read" permissions
  assert len(documents) == 0

  # multi-model queries still work without authorization
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
  subquery = oso_session.query(Document.id).filter(Document.is_public).scalar_subquery()
  documents = (
      oso_session.query(Document)
      .authorized(alice, "read")
      .filter(Document.id.in_(subquery))
      .all()
  )
  assert len(documents) > 0
  assert all(document.is_public for document in documents)  # All returned documents should be public

  count_query = oso_session.query(Document.status, func.count(Document.id).label('count')).group_by(Document.status).authorized(alice, "read") 
  count_results = count_query.all()
  assert len(count_results) > 0 

def test_authorized_on_column(oso_session: sqlalchemy_oso_cloud.Session, alice: Value):
  documents = oso_session.query(Document.id).authorized(alice, "read").all() 
  assert len(documents) > 0
  assert all(isinstance(doc.id, int) for doc in documents)
