from typing import TypeVar

import sqlalchemy.sql
from oso_cloud import Value

from .auth import _apply_authorization_options

Self = TypeVar("Self", bound="Select")

class Select(sqlalchemy.sql.Select):
    """A Select subclass that adds authorization functionality"""

    inherit_cache = True
    """Internal SQLAlchemy caching optimization"""
    
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def authorized(self: Self, actor: Value, action: str) -> Self:
        """Add authorization filtering to the select statement"""
        return _apply_authorization_options(self, actor, action)
    
    
def select(*args, **kwargs) -> Select:
    """
    Create an sqlalchemy_oso_cloud.Select() object

    This is a drop-in replacement for sqlalchemy.select() that adds
    authorization capabilities via the .authorized() method.
    
    Example:
        from sqlalchemy_oso_cloud import select

        stmt = select(Document).where(Document.private == True).authorized(actor, "read")
        documents = session.execute(stmt)
    """
    return Select(*args, **kwargs)
