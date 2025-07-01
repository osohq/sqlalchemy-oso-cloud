import sqlalchemy.orm
from sqlalchemy.orm import with_loader_criteria
from sqlalchemy import text, select
from oso_cloud import Value
from typing import TypeVar, Self
from .oso import get_oso

T = TypeVar("T")

# todo - multiple permissions for multiple main models
class Query(sqlalchemy.orm.Query[T]):
  def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)
      self.oso = get_oso()
      self.filter_cache = {}

  def authorized_for(self, actor: Value, action: str) -> Self:
    models = self._extract_unique_models()
    options = []

    for model in models:
        auth_criteria = self._create_auth_criteria_for_model(model, actor, action)
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
  


  def _create_auth_criteria_for_model(self, model, actor: Value, action: str):
        """Create auth criteria - cache expensive oso.list_local() calls"""
        cache_key = f"{model.__name__}:{actor.id}:{action}"

        if cache_key not in self.filter_cache:
            sql_filter = self.oso.list_local(
                actor=actor,
                action=action,
                resource_type=model.__name__,
                column=f"{model.__tablename__}.id"
            )
            
            auth_subquery = select(model.id).where(text(sql_filter))
            criteria = model.id.in_(auth_subquery)
            
            self.filter_cache[cache_key] = criteria
        
        criteria = self.filter_cache[cache_key]

        return lambda cls: criteria
  