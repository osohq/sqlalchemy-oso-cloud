from sqlalchemy.sql import Select
from sqlalchemy import select as sqlalchemy_select, text
from sqlalchemy.orm import DeclarativeBase, with_loader_criteria
from oso_cloud import Value
from typing import Any, Self, Union, Type
from .oso import get_oso

class AuthorizedSelect(Select):
    """A Select subclass that adds authorization functionality"""

    inherit_cache = True
    
    def __init__(self, *args, **kwargs):
        # Handle case where we're wrapping an existing Select
        if len(args) == 1 and isinstance(args[0], Select):
            select_stmt = args[0]
            # Copy the select statement's internal state
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

    def _create_auth_filter(self, model: Type[DeclarativeBase], actor: Value, action: str):
        """Create authorization filter for a model, with caching"""
        cache_key = f"{model.__name__}:{actor.id}:{action}"
        
        if cache_key not in self._auth_cache:
            sql_filter = self._oso.list_local(
                actor=actor,
                action=action,
                resource_type=model.__name__,
                column=f"{model.__tablename__}.id"
            )
            
            auth_subquery = sqlalchemy_select(model.id).where(text(sql_filter))
            self._auth_cache[cache_key] = model.id.in_(auth_subquery)
        
        criteria = self._auth_cache[cache_key]

        return lambda cls: criteria
    
    def _extract_unique_models(self):
        """Extract all models being queried"""
        models = set()
        
        for desc in self.column_descriptions:
            if desc['entity'] is not None:
                models.add(desc['entity'])
        return models
        
    def _get_model_from_column(self, column):
        """Extract model class from a column"""
        # Direct entity reference (common case)
        if hasattr(column, 'entity'):
            return column['entity']
        
        # Column from a table
        if hasattr(column, 'table'):
            return self._get_model_from_table(column.table)
        
        # InstrumentedAttribute case
        if hasattr(column, 'class_'):
            return column.class_
            
        return None
    
    def _get_model_from_table(self, table):
        """Extract model class from a table"""
        if not hasattr(table, '_sa_registry'):
            return None
            
        # Search through the registry to find the model for this table
        registry = table._sa_registry
        for mapper in registry.mappers:
            if hasattr(mapper, 'class_') and hasattr(mapper.class_, '__table__'):
                if mapper.class_.__table__ is table:
                    return mapper.class_
        
        return None
    
    def __getattr__(self, name: str) -> Any:
        """Delegate to parent Select and wrap any Select results"""
        # Get the attribute from the parent Select class
        attr = getattr(super(), name)
        
        # If it's a callable method, wrap it to handle Select returns
        if callable(attr):
            def wrapper(*args, **kwargs):
                result = attr(*args, **kwargs)
                # If the method returns a Select, wrap it in AuthorizedSelect
                if isinstance(result, Select) and not isinstance(result, AuthorizedSelect):
                    wrapped = AuthorizedSelect(result)
                    # Preserve the auth cache from the current instance
                    wrapped._auth_cache = self._auth_cache.copy()
                    return wrapped
                return result
            return wrapper
        
        # For non-callable attributes, just return as-is
        return attr

def select(*args, **kwargs) -> AuthorizedSelect:
    """Create an AuthorizedSelect statement
    
    This is a drop-in replacement for sqlalchemy.select() that adds
    authorization capabilities via the .authorized_for() method.
    
    Example:
        from sqlalchemy_oso_cloud import select
        
        stmt = select(User).where(User.active == True).authorized_for(actor, "read")
        users = session.execute(stmt)
    """
    return AuthorizedSelect(*args, **kwargs)