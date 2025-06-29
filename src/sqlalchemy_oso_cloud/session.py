import sqlalchemy.orm
from .query import Query
from typing import Type, TypeVar

T = TypeVar("T")

class Session(sqlalchemy.orm.Session):
  """
  A convenience wrapper around SQLAlchemy's built-in
  [`sqlalchemy.orm.Session`](https://docs.sqlalchemy.org/orm/session_api.html#sqlalchemy%2Eorm%2ESession)
  class.
  
  This class extends SQLAlchemy's Session to automatically use our custom `.Query` class
  instead of the default [`sqlalchemy.orm.Query`](https://docs.sqlalchemy.org/orm/queryguide/query.html#sqlalchemy%2Eorm%2EQuery) class.
  This is only useful if you intend to use SQLAlchemy's [legacy Query API](https://docs.sqlalchemy.org/orm/queryguide/query.html).
  """
  _query_cls: Type[Query] = Query

  def __init__(self, *args, **kwargs):
    """
    Initialize a SQLAlchemy session with the `.Query` class extended to support authorization.
    Accepts all of the same arguments as [`sqlalchemy.orm.Session`](https://docs.sqlalchemy.org/orm/session_api.html#sqlalchemy%2Eorm%2ESession),
    except for `query_cls`.
    """
    if "query_cls" in kwargs:
      raise ValueError("sqlalchemy_oso_cloud does not currently support combining with other query classes")
    super().__init__(*args, **{ **kwargs, "query_cls": Query })

  # TODO(connor): arguments/types to support original query method
  def query(self, entity: Type[T], *args, **kwargs) -> Query[T]:  # type: ignore
    """
    Returns a SQLAlchemy query extended to support authorization.
    Accepts all of the same arguments as
    [`sqlalchemy.orm.Session.query`](https://docs.sqlalchemy.org/en/20/orm/session_api.html#sqlalchemy%2Eorm%2ESession%2Equery).
    """
    return super().query(entity, *args, **kwargs)
