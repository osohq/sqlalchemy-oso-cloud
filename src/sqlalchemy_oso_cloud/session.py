from typing import Any, Tuple, Type, TypeVar, Union, overload

import sqlalchemy.orm
from sqlalchemy.engine import Row
from sqlalchemy.orm.attributes import InstrumentedAttribute

from .query import Query

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

   # Two arguments - any combination of entities/columns
  @overload
  def query(self, 
           arg1: Union[Type[T1], InstrumentedAttribute[T1]], 
           arg2: Union[Type[T2], InstrumentedAttribute[T2]], /) -> Query[Row[Tuple[T1, T2]]]: ...

  # Three arguments - any combination of entities/columns
  @overload
  def query(self, 
           arg1: Union[Type[T1], InstrumentedAttribute[T1]], 
           arg2: Union[Type[T2], InstrumentedAttribute[T2]], 
           arg3: Union[Type[T3], InstrumentedAttribute[T3]], /) -> Query[Row[Tuple[T1, T2, T3]]]: ...

  # Four arguments - any combination of entities/columns
  @overload
  def query(self, 
           arg1: Union[Type[T1], InstrumentedAttribute[T1]], 
           arg2: Union[Type[T2], InstrumentedAttribute[T2]], 
           arg3: Union[Type[T3], InstrumentedAttribute[T3]], 
           arg4: Union[Type[T4], InstrumentedAttribute[T4]], /) -> Query[Row[Tuple[T1, T2, T3, T4]]]: ...


  # Fallback overload
  @overload
  def query(self, *entities: Any) -> Query[Any]: ...

  def query(self, *entities, **kwargs) -> Query[Any]:
      """
      Returns a SQLAlchemy query extended to support authorization.

      Returns a SQLAlchemy query extended to support authorization.
      Accepts all of the same arguments as
      [`sqlalchemy.orm.Session.query`](https://docs.sqlalchemy.org/en/20/orm/session_api.html#sqlalchemy%2Eorm%2ESession%2Equery).
    
      Single entity queries return Query[T].
      Multi-entity and column queries return Query[Row[Tuple[...]]].
      All other queries types return Query[Any].
      """
      return super().query(*entities, **kwargs)
