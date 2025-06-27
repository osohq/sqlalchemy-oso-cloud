import os
import yaml

from typing import TypedDict
from oso_cloud import Oso
from sqlalchemy import select
from sqlalchemy.orm import Mapper, registry, ColumnProperty, Relationship
from sqlalchemy.sql.elements import NamedColumn
from tempfile import NamedTemporaryFile

from .orm import ATTRIBUTE_INFO_KEY, Resource, RELATION_INFO_KEY

class FactConfig(TypedDict):
  query: str

class LocalAuthorizationConfig(TypedDict):
  facts: dict[str, FactConfig]
  sql_types: dict[str, str]

def generate_local_authorization_config(registry: registry) -> LocalAuthorizationConfig:
  facts: dict[str, FactConfig] = {}
  sql_types: dict[str, str] = {}

  for mapper in registry.mappers:
    if not issubclass(mapper.class_, Resource):
      continue
    id = mapper.get_property("id")
    if not isinstance(id, ColumnProperty):
      raise ValueError("Oso id must be a column")
    if len(id.columns) != 1:
      raise ValueError("Oso id must be a single column")
    id_column = id.columns[0]
    sql_types[mapper.class_.__name__] = str(id_column.type)
    for attr in mapper.attrs:
      if isinstance(attr, Relationship) and RELATION_INFO_KEY in attr.info:
        key, query = gen_relation_binding(attr, mapper, id_column)
        facts[key] = query
      elif isinstance(attr, ColumnProperty) and ATTRIBUTE_INFO_KEY in attr.columns[0].info:
        key, query = gen_attribute_binding(attr, mapper, id_column)
        sql_types[attr.key.capitalize()] = str(attr.columns[0].type)
        facts[key] = query

  return {
    "facts": facts,
    "sql_types": sql_types,
  }

def gen_relation_binding(relationship: Relationship, mapper: Mapper, id_column: NamedColumn) -> tuple[str, FactConfig]:
  if len(relationship.local_columns) != 1:
    raise ValueError(f"Oso relation {relationship.key} must be to a single column")
  local_column = list(relationship.local_columns)[0]
  key = f"has_relation({mapper.class_.__name__}:_, {relationship.key}, {relationship.entity.class_.__name__}:_)"
  query = select(id_column, local_column)
  return key, {
    "query": str(query),
  }

def gen_attribute_binding(attribute: ColumnProperty, mapper: Mapper, id_column: NamedColumn) -> tuple[str, FactConfig]:
  if len(attribute.columns) != 1:
    raise ValueError(f"Oso attribute {attribute.key} must be a single column")
  column = attribute.columns[0]
  key = f"has_{attribute.key}({mapper.class_.__name__}:_, {attribute.key.capitalize()}:_)"
  query = select(id_column, column)
  return key, {
    "query": str(query),
  }


# TODO: what if they want multiple DBs/registries?
oso: Oso | None = None

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
    config = generate_local_authorization_config(registry)
    yaml.dump(config, f)
    f.flush()
    kwargs["data_bindings"] = f.name
    global oso
    oso = Oso(**kwargs)
  
def get_oso() -> Oso:
  if oso is None:
    raise RuntimeError("sqlalchemy_oso_cloud must be initialized before getting the Oso client")
  return oso
