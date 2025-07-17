import os
import yaml
from enum import Enum

from typing import TypedDict, Optional, Union
from oso_cloud import Oso
from sqlalchemy import select
from sqlalchemy.orm import Mapper, RelationshipProperty, registry, ColumnProperty
from sqlalchemy.sql.elements import NamedColumn
from sqlalchemy.sql.sqltypes import Boolean, Integer, String, TypeEngine
from tempfile import NamedTemporaryFile

from .orm import _ATTRIBUTE_INFO_KEY, Resource, _RELATION_INFO_KEY, _REMOTE_RELATION_INFO_KEY, HasRole
from .orm import _ROLE_MAPPING_ACTOR_INFO_KEY, _ROLE_MAPPING_ROLE_INFO_KEY, _ROLE_MAPPING_RESOURCE_INFO_KEY

class FactConfig(TypedDict):
  query: str

class LocalAuthorizationConfig(TypedDict):
  facts: dict[str, FactConfig]
  sql_types: dict[str, str]

def generate_local_authorization_config(registry: registry) -> LocalAuthorizationConfig:
  facts: dict[str, FactConfig] = {}
  sql_types: dict[str, str] = {}

  for mapper in registry.mappers:
    if issubclass(mapper.class_, HasRole):
      bindings, new_sql_types = gen_has_role_binding(mapper)
      facts.update(bindings)
      sql_types.update(new_sql_types)
      continue
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

class HasRoleType(Enum):
  ACTOR = "actor"
  ROLE = "role"
  RESOURCE = "resource"

def _get_oso_type_from_fk(column: NamedColumn, registry: registry, info_key: str, role_mapping_type: HasRoleType) -> str:
  """
  Get the Oso type for a column - this is the type used in the `has_role` fact.
  """
  foreign_keys = list(column.foreign_keys)
  oso_type: Optional[str] = None
  if len(foreign_keys) == 0:
    if role_mapping_type == HasRoleType.ROLE:
      return "String"
    if column.info[info_key] is None:
      raise ValueError(f"Oso role mapping {role_mapping_type} type must be provided if it is not a foreign key")
    oso_type = column.info[info_key]
  else:
    if column.info[info_key] is not None:
      raise ValueError(f"Oso role mapping {role_mapping_type} cannot be provided if the column is a foreign key")
    fk = foreign_keys[0].column
    oso_type = None
    # get the ORM class name for the table that the foreign key points to
    for m in registry.mappers:
      if m.local_table == fk.table:
        oso_type = m.class_.__name__
        if not issubclass(m.class_, Resource):
          if role_mapping_type != HasRoleType.ROLE:
            raise ValueError(f"Oso role mapping {role_mapping_type} must be an Oso Resource")
          elif role_mapping_type == HasRoleType.ROLE:
            # if the role is not defined in the model as an Oso Resource, it will be a String type in the has_role fact
            return "String"
        break
  if oso_type is None:
    raise ValueError(f"Oso role mapping {role_mapping_type} type could not be determined")
  return oso_type

def gen_has_role_binding(mapper: Mapper) -> tuple[dict[str, FactConfig], dict[str, str]]:
  has_role_columns: dict[HasRoleType, NamedColumn] = {}
  has_role_types: dict[HasRoleType, str] = {}
  sql_types: dict[str, str] = {}

  for attr in mapper.attrs:
    if isinstance(attr, ColumnProperty) and any(info_key in attr.columns[0].info for info_key in [_ROLE_MAPPING_ROLE_INFO_KEY, _ROLE_MAPPING_RESOURCE_INFO_KEY, _ROLE_MAPPING_ACTOR_INFO_KEY]):
      if len(attr.columns) != 1:
        raise ValueError(f"Oso role mapping attribute {attr.key} must be a single column")
      for info_key, role_mapping_type in [(_ROLE_MAPPING_ACTOR_INFO_KEY, HasRoleType.ACTOR), (_ROLE_MAPPING_ROLE_INFO_KEY, HasRoleType.ROLE), (_ROLE_MAPPING_RESOURCE_INFO_KEY, HasRoleType.RESOURCE)]:
        if info_key in attr.columns[0].info:
          if info_key in has_role_columns:
            raise ValueError("Oso role mapping can only have a single column for each role mapping type")
          column = attr.columns[0]
          oso_type = _get_oso_type_from_fk(column, mapper.registry, info_key, role_mapping_type)
          has_role_types[role_mapping_type] = oso_type
          if oso_type != "String":
            sql_types[oso_type] = str(column.type)
          has_role_columns[role_mapping_type] = column

  if has_role_columns[HasRoleType.ACTOR] is None:
    raise ValueError("Oso role mapping must have an actor column")
  if has_role_columns[HasRoleType.ROLE] is None or not isinstance(has_role_columns[HasRoleType.ROLE].type, String):
    raise ValueError("Oso role mapping must have a role column of type String")
  if has_role_columns[HasRoleType.RESOURCE] is None:
    raise ValueError("Oso role mapping must have a resource column")

  key = f"has_role({has_role_types[HasRoleType.ACTOR]}:_, {has_role_types[HasRoleType.ROLE]}:_, {has_role_types[HasRoleType.RESOURCE]}:_)"
  bindings: dict[str, FactConfig] = {
    key: {
      "query": str(select(has_role_columns[HasRoleType.ACTOR], has_role_columns[HasRoleType.ROLE], has_role_columns[HasRoleType.RESOURCE])),
    }
  }
  return bindings, sql_types

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
    kwargs["api_key"] = os.getenv("OSO_AUTH")
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
