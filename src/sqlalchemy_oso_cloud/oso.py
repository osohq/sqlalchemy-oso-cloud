import os
import yaml

from typing import TypedDict, Optional, Union
from oso_cloud import Oso
from sqlalchemy import select
from sqlalchemy.orm import Mapper, RelationshipProperty, registry, ColumnProperty
from sqlalchemy.sql.elements import NamedColumn
from sqlalchemy.sql.sqltypes import Boolean, Integer, String, TypeEngine
from tempfile import NamedTemporaryFile

from .orm import _ATTRIBUTE_INFO_KEY, Resource, _RELATION_INFO_KEY, _REMOTE_RELATION_INFO_KEY

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
      if isinstance(attr, RelationshipProperty) and _RELATION_INFO_KEY in attr.info:
        bindings = gen_relation_binding(attr, mapper, id_column)
        facts.update(bindings)
      elif isinstance(attr, ColumnProperty):
        if _ATTRIBUTE_INFO_KEY in attr.columns[0].info:
          bindings = gen_attribute_binding(attr, mapper, id_column)
          facts.update(bindings)
        elif _REMOTE_RELATION_INFO_KEY in attr.columns[0].info:
          remote_resource_name, remote_relation_key = attr.columns[0].info[_REMOTE_RELATION_INFO_KEY]
          sql_types[remote_resource_name] = str(attr.columns[0].type)
          bindings = gen_remote_relation_binding(attr, mapper, id_column, remote_resource_name, remote_relation_key)
          facts.update(bindings)

  return {
    "facts": facts,
    "sql_types": sql_types,
  }

def gen_relation_binding(relationship: RelationshipProperty, mapper: Mapper, id_column: NamedColumn) -> dict[str, FactConfig]:
  remote = relationship.entity
  remote_id = remote.get_property("id")
  if not isinstance(remote_id, ColumnProperty):
    raise ValueError("Oso relation id must be a column")
  if len(remote_id.columns) != 1:
    raise ValueError("Oso relation id must be a single column")
  remote_id_column = remote_id.columns[0]
  key = f"has_relation({mapper.class_.__name__}:_, {relationship.key}, {remote.class_.__name__}:_)"
  query = select(id_column, remote_id_column).where(relationship.primaryjoin)
  return {
    key: {
      "query": str(query),
    }
  }

def gen_attribute_binding(attribute: ColumnProperty, mapper: Mapper, id_column: NamedColumn) -> dict[str, FactConfig]:
  if len(attribute.columns) != 1:
    raise ValueError(f"Oso attribute {attribute.key} must be a single column")
  column = attribute.columns[0]
  key_type = to_polar_type(column.type)
  
  if key_type == "Boolean":
    key = f"{attribute.key}({mapper.class_.__name__}:_)"
    return {
      key: {
        "query": str(select(id_column).where(column)),
      }
    }
    
  key = f"has_{attribute.key}({mapper.class_.__name__}:_, {key_type}:_)"
  return {
    key: {
      "query": str(select(id_column, column)),
    }
  }

def gen_remote_relation_binding(attribute: ColumnProperty, mapper: Mapper, id_column: NamedColumn, remote_resource_name: str, remote_relation_key: Union[str, None]) -> dict[str, FactConfig]:
  if len(attribute.columns) != 1:
    raise ValueError(f"Oso remote relation {attribute.key} must be a single column")
  column = attribute.columns[0]
  if remote_relation_key is None:
    remote_relation_key = column.name.removesuffix("_id")
  key = f"has_relation({mapper.class_.__name__}:_, {remote_relation_key}, {remote_resource_name}:_)"
  return {
    key: {
      "query": str(select(id_column, column)),
    }
  }

def to_polar_type(column_type: TypeEngine) -> str:
  if isinstance(column_type, Integer):
    return "Integer"
  elif isinstance(column_type, String):
    return "String"
  elif isinstance(column_type, Boolean):
    return "Boolean"
  else:
    raise ValueError(f"Unsupported type: {column_type}")


# TODO: what if they want multiple DBs/registries?
oso: Optional[Oso] = None

def init(registry: registry, **kwargs):
  """
  Initialize an Oso Cloud client configured to resolve authorization data from your
  database as specified in your ORM models.
  See `.orm` for more information on how to map your authorization data.

  :param registry: The SQLAlchemy registry containing your models. For example, `Base.registry`.
  :param kwargs: Additional keyword arguments to pass to the Oso client constructor, such as `url` and `api_key`.
  """
  global oso
  if oso is not None:
    raise RuntimeError("sqlalchemy_oso_cloud has already been initialized")
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
    oso = Oso(**kwargs)
  
def get_oso() -> Oso:
  """
  Get the Oso Cloud client that was created with `init`.

  :return: The Oso Cloud client.
  """
  global oso
  if oso is None:
    raise RuntimeError("sqlalchemy_oso_cloud must be initialized before getting the Oso client")
  return oso
