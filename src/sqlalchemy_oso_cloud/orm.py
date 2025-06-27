from sqlalchemy.orm import MappedColumn, Relationship, mapped_column, relationship

class Resource:
  pass

RELATION_INFO_KEY = "_oso.relation"
ATTRIBUTE_INFO_KEY = "_oso.attribute"

def relation(*args, **kwargs) -> Relationship:
  rel = relationship(*args, **kwargs)
  rel.info[RELATION_INFO_KEY] = None
  return rel

def attribute(*args, **kwargs) -> MappedColumn:
  col = mapped_column(*args, **kwargs)
  col.column.info[ATTRIBUTE_INFO_KEY] = None
  return col