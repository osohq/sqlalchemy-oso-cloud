"""
Utilities for [declaratively mapping](https://docs.sqlalchemy.org/en/20/orm/mapping_styles.html#orm-declarative-mapping)
[authorization data](https://www.osohq.com/docs/authorization-data) in your ORM models.
"""

from sqlalchemy.orm import MappedColumn, Relationship, mapped_column, relationship
from typing import Union

class Resource:
  """
  A mixin to indicate that an ORM model corresponds to an Oso resource.
  """
  pass

_RELATION_INFO_KEY = "_oso.relation"
_ATTRIBUTE_INFO_KEY = "_oso.attribute"
_REMOTE_RELATION_INFO_KEY = "_oso.remote_relation"

def relation(*args, **kwargs) -> Relationship:
  """
  A wrapper around [`sqlalchemy.orm.relationship`](https://docs.sqlalchemy.org/en/20/orm/relationship_api.html#sqlalchemy.orm.relationship)
  that indicates that the relationship corresponds to `has_relation` facts in Oso with the following three arguments:
  1. the resource this relationship is declared on,
  2. the name of this relationship, and
  3. the resource that the relationship points to.

  Accepts all of the same arguments as [`sqlalchemy.orm.relationship`](https://docs.sqlalchemy.org/en/20/orm/relationship_api.html#sqlalchemy.orm.relationship).
  """
  rel = relationship(*args, **kwargs)
  rel.info[_RELATION_INFO_KEY] = None
  return rel

def attribute(*args, **kwargs) -> MappedColumn:
  """
  A wrapper around [`sqlalchemy.orm.mapped_column`](https://docs.sqlalchemy.org/en/20/orm/mapping_api.html#sqlalchemy.orm.mapped_column)
  that indicates that the attribute corresponds to `has_{attribute_name}` facts in Oso with the following two arguments:
  1. the resource this attribute is declared on, and
  2. the attribute value.

  Accepts all of the same arguments as [`sqlalchemy.orm.mapped_column`](https://docs.sqlalchemy.org/en/20/orm/mapping_api.html#sqlalchemy.orm.mapped_column).
  """
  col = mapped_column(*args, **kwargs)
  col.column.info[_ATTRIBUTE_INFO_KEY] = None
  return col

def remote_relation(remote_resource_name: str, remote_relation_key: Union[str, None] = None, *args, **kwargs) -> MappedColumn:
  """
  A wrapper around [`sqlalchemy.orm.mapped_column`](https://docs.sqlalchemy.org/en/20/orm/mapping_api.html#sqlalchemy.orm.mapped_column)
  that indicates that the attribute corresponds to `has_relation` facts (to a resource not defined in the local database) in Oso with the following two arguments:
  1. the resource this attribute is declared on, and
  2. the name of this relationship, and
  3. the resource that the relationship points to.

  Note: this is not a [`sqlalchemy.orm.relationship`](https://docs.sqlalchemy.org/en/20/orm/relationship_api.html#sqlalchemy.orm.relationship).

  Accepts all of the same arguments as [`sqlalchemy.orm.mapped_column`](https://docs.sqlalchemy.org/en/20/orm/mapping_api.html#sqlalchemy.orm.mapped_column).
  Also accepts the following additional arguments:
  :param remote_resource_name: the name of the remote resource
  :param remote_relation_key: (optional) the name of the relation on the remote resource. If not provided, the name of the relation will be inferred from the name of the column.
  """
  col = mapped_column(*args, **kwargs)
  col.column.info[_REMOTE_RELATION_INFO_KEY] = (remote_resource_name, remote_relation_key)
  return col