import socket

import pytest
from oso_cloud import Oso, Value
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from testcontainers.core.container import DockerContainer  # type: ignore
from testcontainers.core.waiting_utils import (  # type: ignore
  wait_container_is_ready,
  wait_for,
)
from testcontainers.postgres import PostgresContainer  # type: ignore

import sqlalchemy_oso_cloud

from .models import Base, Document, Organization


@pytest.fixture(scope="session")
def oso_dev_server():
  container = DockerContainer("public.ecr.aws/osohq/dev-server:latest").with_exposed_ports(8080)
  container.start()
  host = container.get_container_host_ip()
  port = container.get_exposed_port(8080)
  def is_ready():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
      sock.connect((host, int(port)))
  wait_for(is_ready)
  yield container
  container.stop()

@pytest.fixture(scope="session")
def postgres():
  container = PostgresContainer(
    image="pgvector/pgvector:pg17",
    username="test",
    password="test",
    dbname="test"
  )
  container.start()
  yield container
  container.stop()

@pytest.fixture(scope="session")
def engine(postgres: PostgresContainer):
  # for some reason, the waiting already built into PostgresContainer.start() is insufficient
  @wait_container_is_ready(OperationalError)
  def create_tables():
    with engine.connect() as conn:
      conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
      conn.commit()
    Base.metadata.create_all(engine)

  engine = create_engine(postgres.get_connection_url())
  create_tables()
  return engine


@pytest.fixture
def session(engine: Engine):
  with Session(engine) as session:
    yield session

@pytest.fixture(scope="session")
def oso_url(oso_dev_server: DockerContainer):
  host = oso_dev_server.get_container_host_ip()
  port = oso_dev_server.get_exposed_port(8080)
  return f"http://{host}:{port}"

@pytest.fixture(scope="session")
def oso_auth():
  return "e_0123456789_12345_osotesttoken01xiIn"

@pytest.fixture(scope="session")
def oso(oso_url: str, oso_auth: str):
  # TODO: move client init into the library itself, since it'll need to init the Oso client itself to provide the data bindings
  oso = Oso(oso_url, oso_auth, data_bindings="tests/data.yaml") 
  with open("tests/policy.polar", "r") as f:
    oso.policy(f.read())
  return oso

@pytest.fixture
def alice():
  # TODO: make our mixin automatically turn the model classes into Oso Values
  return Value("User", "alice")

@pytest.fixture
def bob():
  return Value("User", "bob")

@pytest.fixture(autouse=True)
def setup_oso_data(oso: Oso, alice: Value, bob: Value):
  alice_role = ("has_role", alice, "admin", Value("Organization", "1"))
  bob_role = ("has_role", bob, "admin", Value("Organization", "2"))
  alice_team_role = ("has_role", alice, "editor", Value("Team", "111"))
  bob_team_role = ("has_role", bob, "editor", Value("Team", "222"))
  oso.insert(alice_role)
  oso.insert(bob_role)
  oso.insert(alice_team_role)
  oso.insert(bob_team_role)
  yield
  oso.delete(alice_role)
  oso.delete(bob_role)
  oso.delete(alice_team_role)
  oso.delete(bob_team_role)

@pytest.fixture(autouse=True)
def setup_postgres_data(session: Session):
  org1 = Organization(id=1, name="acme")
  org2 = Organization(id=2, name="bigco")
  org3 = Organization(id=3, name="cosmo")
  doc1 = Document(id=1, organization=org1, content="hello", status="draft", is_public=False, team_id=111)
  doc2 = Document(id=2, organization=org2, content="world", status="published", is_public=False, team_id=111)
  doc3 = Document(id=3, organization=org3, content="world", status="published", is_public=True, team_id=222)

  doc1.embedding = [0.1, 0.2, 0.3]
  doc2.embedding = [0.4, 0.5, 0.6]
  doc3.embedding = [0.7, 0.8, 0.9]

  session.add(org1)
  session.add(org2)
  session.add(org3)
  session.add(doc1)
  session.add(doc2)
  session.add(doc3)
  session.commit()
  yield
  session.delete(org1)
  session.delete(org2)
  session.delete(org3)
  session.delete(doc1)
  session.delete(doc2)
  session.delete(doc3)
  session.commit()

@pytest.fixture(autouse=True, scope="session")
def init_sqlalchemy_oso_cloud(oso_url: str, oso_auth: str):
  sqlalchemy_oso_cloud.init(Base.registry, url=oso_url, api_key=oso_auth)

@pytest.fixture
def oso_session(engine: Engine):
  with sqlalchemy_oso_cloud.Session(engine) as session:
    yield session
