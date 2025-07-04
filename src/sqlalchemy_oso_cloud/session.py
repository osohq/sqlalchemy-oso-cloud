import sqlalchemy.orm
from .query import Query
from sqlalchemy.engine import Row
from sqlalchemy.orm.attributes import InstrumentedAttribute
from typing import Type, TypeVar, overload, Any, Tuple

T = TypeVar("T")
T1 = TypeVar("T1")
T2 = TypeVar("T2")
T3 = TypeVar("T3")
T4 = TypeVar("T4")

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

  # Single entity overload
  @overload # type: ignore[override]
  def query(self, entity: Type[T], /) -> Query[T]: ...

  # Single column overload
  @overload
  def query(self, column: InstrumentedAttribute[T], /) -> Query[Row[Tuple[T]]]: ...

  # Two entities overload
  @overload
  def query(self, entity1: Type[T1], entity2: Type[T2], /) -> Query[Row[Tuple[T1, T2]]]: ...

  # Two columns overload
  @overload
  def query(self, col1: InstrumentedAttribute[T1], col2: InstrumentedAttribute[T2], /) -> Query[Row[Tuple[T1, T2]]]: ...

  # Mixed: entity + column
  @overload
  def query(self, entity: Type[T1], column: InstrumentedAttribute[T2], /) -> Query[Row[Tuple[T1, T2]]]: ...

  # Three entities overload
  @overload
  def query(self, entity1: Type[T1], entity2: Type[T2], entity3: Type[T3], /) -> Query[Row[Tuple[T1, T2, T3]]]: ...

  # Four entities overload
  @overload
  def query(self, entity1: Type[T1], entity2: Type[T2], entity3: Type[T3], entity4: Type[T4], /) -> Query[Row[Tuple[T1, T2, T3, T4]]]: ...

  # Fallback overload
  @overload
  def query(self, *entities: Any) -> Query[Any]: ...

  def query(self, *entities, **kwargs) -> Query[Any]:
      """
      Returns a SQLAlchemy query extended to support authorization.

      Single entity queries which return Query[T].
      Multi-entity and column queries return Query[Row[Tuple[...]]].
      All other queries types return Query[Any].
      """
      return super().query(*entities, **kwargs)
