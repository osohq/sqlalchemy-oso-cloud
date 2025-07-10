import sqlalchemy.sql
from sqlalchemy.orm.attributes import InstrumentedAttribute
from oso_cloud import Value
from typing import  TypeVar, Generic, Any, overload, Type, Tuple, Union
from .auth import _apply_authorization_options

Self = TypeVar("Self", bound="Select")
_T = TypeVar("_T", bound=Tuple[Any, ...])
T = TypeVar("T")
T1 = TypeVar("T1")
T2 = TypeVar("T2")
T3 = TypeVar("T3")
T4 = TypeVar("T4")

class Select(sqlalchemy.sql.Select[_T], Generic[_T]):
    """A Select subclass that adds authorization functionality"""

    inherit_cache = True
    """Internal SQLAlchemy caching optimization"""
    
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def authorized(self: Self, actor: Value, action: str) -> Self:
        """Add authorization filtering to the select statement"""
        return _apply_authorization_options(self, actor, action)

# Single entity overload
@overload
def select(entity: Type[T]) -> Select[Tuple[T]]: ...

# Single column overload
@overload
def select(column: InstrumentedAttribute[T]) -> Select[Tuple[T]]: ...

@overload
def select(
    arg1: Union[Type[T1], InstrumentedAttribute[T1]], 
    arg2: Union[Type[T2], InstrumentedAttribute[T2]]) -> Select[Tuple[T1, T2]]: ...

@overload
def select(arg1: Union[Type[T1], InstrumentedAttribute[T1]], 
           arg2: Union[Type[T2], InstrumentedAttribute[T2]], 
           arg3: Union[Type[T3], InstrumentedAttribute[T3]]) -> Select[Tuple[T1, T2, T3]]: ...

@overload
def select(arg1: Union[Type[T1], InstrumentedAttribute[T1]], 
           arg2: Union[Type[T2], InstrumentedAttribute[T2]], 
           arg3: Union[Type[T3], InstrumentedAttribute[T3]], 
           arg4: Union[Type[T4], InstrumentedAttribute[T4]]) -> Select[Tuple[T1, T2, T3, T4]]: ...

@overload
def select(*entities: Any) -> Select[Any]: ...    
def select(*entities, **kwargs) -> Select[Any]:
    """
    Create an sqlalchemy_oso_cloud.Select() object

    This is a drop-in replacement for sqlalchemy.select() that adds
    authorization capabilities via the .authorized() method.
    
    Example:
        from sqlalchemy_oso_cloud import select

        stmt = select(Document).where(Document.private == True).authorized(actor, "read")
        documents = session.execute(stmt)
    """
    return Select(*entities, **kwargs)
