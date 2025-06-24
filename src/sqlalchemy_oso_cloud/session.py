import sqlalchemy.orm
from .query import Query
from typing import Type, Any, TypeVar, Union


T = TypeVar("T")

class Session(sqlalchemy.orm.Session):
  _query_cls: Type[Query] = Query

  def __init__(self, *args, **kwargs):
    if "query_cls" in kwargs:
      raise ValueError("sqlalchemy_oso_cloud does not currently support combining with other query classes")
    super().__init__(*args, **{ **kwargs, "query_cls": Query })

  def query(self, entity: Type[T], *args, **kwargs) -> Query[T]:  # type: ignore
    return super().query(entity, *args, **kwargs)
