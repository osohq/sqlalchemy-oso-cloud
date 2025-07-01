from sqlalchemy.sql import Select
from sqlalchemy import select as sqlalchemy_select, literal_column
from sqlalchemy.orm import DeclarativeBase, with_loader_criteria
from oso_cloud import Value
from typing import  Self, Type
from .oso import get_oso

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
        self._auth_cache = {}
    
    def authorized_for(self, actor: Value, action: str) -> Self:
        """Add authorization filtering to the select statement"""
        models = self._extract_unique_models()
        options = []
        
        for model in models:
            auth_criteria = self._create_auth_filter(model, actor, action)
            options.append(
                with_loader_criteria(
                    model,
                    auth_criteria,
                    include_aliases=True
                )
            )
        return self.options(*options)
    
    def _extract_unique_models(self):
        """Extract all models being queried"""
        models = set()
        
        for desc in self.column_descriptions:
            if desc['entity'] is not None:
                models.add(desc['entity'])
        return models

    def _create_auth_filter(self, model: Type[DeclarativeBase], actor: Value, action: str):
        """Create authorization filter for a model"""
        
        sql_filter = self._oso.list_local(
            actor=actor,
            action=action,
            resource_type=model.__name__,
            column=f"{model.__tablename__}.id"
        )
        
        criteria = literal_column(sql_filter)

        return lambda cls: criteria

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