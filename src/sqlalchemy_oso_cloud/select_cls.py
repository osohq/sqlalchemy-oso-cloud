from sqlalchemy.sql import Select
from sqlalchemy import literal_column, ColumnClause
from sqlalchemy.orm import DeclarativeBase, with_loader_criteria
from oso_cloud import Value
from typing import  TypeVar, Type
from .oso import get_oso
from .auth import _apply_authorization_options

Self = TypeVar("Self", bound="AuthorizedSelect")

class AuthorizedSelect(Select):
    """A Select subclass that adds authorization functionality"""

    inherit_cache = True
    
    def __init__(self, *args, **kwargs):
        # Handle case where we're wrapping an existing Select e.g. AuthorizedSelect(existing_Select)
        if len(args) == 1 and isinstance(args[0], Select):
            select_stmt = args[0]
            super().__init__()
            self.__dict__.update(select_stmt.__dict__)
        else:
            super().__init__(*args, **kwargs)
        
        self._oso = get_oso()
    
    def authorized(self: Self, actor: Value, action: str) -> Self:
        """Add authorization filtering to the select statement"""
        return _apply_authorization_options(self, actor, action)
    
    
def select(*args, **kwargs) -> AuthorizedSelect:
    """
    Create an AuthorizedSelect statement
    
    This is a drop-in replacement for sqlalchemy.select() that adds
    authorization capabilities via the .authorized() method.
    
    Example:
        from sqlalchemy_oso_cloud import select

        stmt = select(Document).where(Document.private == True).authorized(actor, "read")
        documents = session.execute(stmt)
    """
    return AuthorizedSelect(*args, **kwargs)
