from testcontainers.core.container import DockerContainer  # type: ignore
from testcontainers.postgres import PostgresContainer  # type: ignore
from sqlalchemy import Engine, create_engine
import pytest
from sqlalchemy.orm import Session
from oso_cloud import Oso, Value

oso_dev_server_container = DockerContainer("public.ecr.aws/osohq/dev-server:latest").with_exposed_ports(8080)
postgres_container = PostgresContainer()

@pytest.fixture(scope="session")
def oso_dev_server():
  oso_dev_server_container.start()
  yield oso_dev_server_container
  oso_dev_server_container.stop()

@pytest.fixture(scope="session")
def postgres():
  postgres_container.start()
  yield postgres_container
  postgres_container.stop()

@pytest.fixture(scope="session")
def engine():
  return create_engine(postgres_container.get_connection_url())

@pytest.fixture(scope="session")
def session(engine: Engine):
  with Session(engine) as session:
    yield session

@pytest.fixture(scope="session", autouse=True)
def oso(oso_dev_server: DockerContainer):
  host = oso_dev_server.get_container_host_ip()
  port = oso_dev_server.get_exposed_port(8080)
  oso_url = f"http://{host}:{port}"
  oso_auth = "e_0123456789_12345_osotesttoken01xiIn"
  # TODO: move this into the library itself, since it'll need to provide the data bindings itself
  return Oso(oso_url, oso_auth, data_bindings="tests/data.yaml") 

@pytest.fixture
def setup_oso_data(oso: Oso):
  # TODO: make our mixin automatically turn the model classes into Oso Values
  oso.insert(("has_role", Value("User", "alice"), "admin", Value("Organization", "acme")))

@pytest.fixture
def setup_postgres_data(session: Session):
  pass # TODO: set up sqlalchemy ORM