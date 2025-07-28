"""
Test compatibility with pgvector-sqlalchemy
"""
import numpy as np
import pytest
from oso_cloud import Value
from sqlalchemy import select as sqla_select
from sqlalchemy import text

from sqlalchemy_oso_cloud import Session as OsoSession
from sqlalchemy_oso_cloud import authorized, select

from .models import Document, Organization

if not hasattr(Document, 'embedding'):
    pytest.skip("Document model doesn't have embedding field", allow_module_level=True)


def test_pgvector_extension_creation(oso_session: OsoSession):
    oso_session.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
    oso_session.commit()
    
    result = oso_session.execute(
        text("SELECT * FROM pg_extension WHERE extname = 'vector'")
    ).fetchone()
    assert result is not None


def test_vector_column_with_oso_authorization_query(oso_session: OsoSession, bob: Value):
    query_vector = [0.3, 0.4, 0.5]
   
    documents = (
        oso_session.query(Document)
        .order_by(Document.embedding.l2_distance(query_vector))
        .authorized(bob, "read")
        .all()
        )
   
    assert len(documents) == 2
    assert documents[0].id == 2 


def test_vector_column_with_oso_authorization_select(oso_session: OsoSession, alice: Value):
    query_vector = [0.3, 0.4, 0.5]
   
    stmt = (
        select(Document)
        .order_by(Document.embedding.l2_distance(query_vector))
        .authorized(alice, "read")
    )
    documents = oso_session.execute(stmt).scalars().all()
    
    assert len(documents) >= 3
    assert documents[0].id == 2


def test_vector_distance_with_filters(oso_session: OsoSession, alice: Value):
    query_vector = [0.5, 0.5, 0.5]
    
    stmt = (
        select(Document)
        .where(Document.status == "published")
        .order_by(Document.embedding.l2_distance(query_vector))
        .authorized(alice, "read")
        .limit(10)
    )
    documents = oso_session.execute(stmt).scalars().all()
    
    assert all(doc.status == "published" for doc in documents)
    assert len(documents) >= 1


def test_cosine_distance_search(oso_session: OsoSession, alice: Value):
    """Test using cosine distance instead of L2"""
    query_vector = [1.0, 0.0, 0.0]
    
    stmt = (
        select(Document)
        .order_by(Document.embedding.cosine_distance(query_vector))
        .authorized(alice, "read")
        .limit(5)
    )
    documents = oso_session.execute(stmt).scalars().all()
    
    assert len(documents) > 0

    documents = (
        oso_session.query(Document)
        .order_by(Document.embedding.cosine_distance(query_vector))
        .authorized(alice, "read")
        .limit(5)
        .all()
    )

    assert len(documents) > 0


def test_vector_within_distance_threshold(oso_session: OsoSession, alice: Value):
    query_vector = [0.5, 0.5, 0.5]
    distance_threshold = 1.0
    
    stmt = (
        select(Document)
        .filter(Document.embedding.l2_distance(query_vector) < distance_threshold)
        .authorized(alice, "read")
    )
    documents = oso_session.execute(stmt).scalars().all()
    
    # Verify all returned documents are within the threshold
    for doc in documents:
        distance = np.linalg.norm(
            np.array(doc.embedding) - np.array(query_vector)
        )
        assert distance < distance_threshold


def test_query_api_with_vectors(oso_session: OsoSession, alice: Value):
    query_vector = [0.3, 0.4, 0.5]
    
    documents = (
        oso_session.query(Document)
        .order_by(Document.embedding.l2_distance(query_vector))
        .authorized(alice, "read")
        .limit(5)
        .all()
    )
    
    assert len(documents) > 0
    if len(documents) > 1:
        # np.linalg.norm() calculates the L2 distance
        # essentially confirming the order_by works
        first_distance = np.linalg.norm(
            np.array(documents[0].embedding) - np.array(query_vector)
        )
        last_distance = np.linalg.norm(
            np.array(documents[-1].embedding) - np.array(query_vector)
        )
        assert first_distance <= last_distance


def test_authorized_as_options_with_vectors(oso_session: OsoSession, alice: Value):
    query_vector = [0.5, 0.5, 0.5]
    
    stmt = (
        sqla_select(Document)
        .order_by(Document.embedding.l2_distance(query_vector))
        .options(authorized(alice, "read", Document))
        .limit(3)
    )
    documents = oso_session.execute(stmt).scalars().all()
    
    assert len(documents) > 0


def test_vector_select_with_joins(oso_session: OsoSession, alice: Value):
    query_vector = [0.5, 0.5, 0.5]
    

    stmt = (
        select(Document)
        .join(Organization)
        .where(Organization.name == "acme")
        .order_by(Document.embedding.l2_distance(query_vector))
        .authorized(alice, "read")
    )
    documents = oso_session.execute(stmt).scalars().all()
        
    assert all(doc.organization.name == "acme" for doc in documents)


def test_max_inner_product_search(oso_session: OsoSession, alice: Value):
    query_vector = [0.5, 0.5, 0.5]
    
    stmt = (
        select(Document)
        .order_by(Document.embedding.max_inner_product(query_vector).desc())
        .authorized(alice, "read")
        .limit(5)
    )
    documents = oso_session.execute(stmt).scalars().all()

    assert len(documents) > 0


def test_no_interference_with_non_vector_queries(oso_session: OsoSession, alice: Value):
    # These should work exactly as before, even with pgvector installed
    documents = oso_session.query(Document).authorized(alice, "read").all()
    assert len(documents) >= 3
    
    stmt = select(Document).where(Document.status == "published").authorized(alice, "read")
    documents = oso_session.execute(stmt).scalars().all() # type: ignore
    assert len(documents) >= 1
    assert all(doc.status == "published" for doc in documents)