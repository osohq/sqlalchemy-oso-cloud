from oso_cloud import Oso
from sqlalchemy.orm import registry
from tempfile import NamedTemporaryFile
import os

# TODO: what if they want multiple DBs/registries?
oso: Oso | None = None

TODO_YAML = """
facts:
  has_relation(Document:_, organization, Organization:_):
    query: SELECT id, organization_id FROM document
"""

def init(registry: registry, **kwargs):
  kwargs = { **kwargs }
  if "url" not in kwargs:
    kwargs["url"] = os.getenv("OSO_URL", "https://api.osohq.com")
  if "api_key" not in kwargs:
    kwargs["api_key"] = os.getenv("OSO_API_KEY")
  if "data_bindings" in kwargs:
    # just need to conditionally close/delete the temporary file if it was created
    raise NotImplementedError("manual data_bindings are not supported yet")
  with NamedTemporaryFile(mode="w") as f:
    f.write(TODO_YAML)
    f.flush()
    kwargs["data_bindings"] = f.name
    global oso
    oso = Oso(**kwargs)
  
def get_oso() -> Oso:
  if oso is None:
    raise RuntimeError("sqlalchemy_oso_cloud must be initialized before getting the Oso client")
  return oso
