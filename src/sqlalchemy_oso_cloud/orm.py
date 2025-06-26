from sqlalchemy.orm import relationship

class Resource:
  pass

RELATION_INFO_KEY = "_oso.relation"

# TODO: should this be on columns or relationships?
# TODO: types
def relation(*args, **kwargs):
  rel = relationship(*args, **kwargs)
  rel.info[RELATION_INFO_KEY] = None
  return rel
