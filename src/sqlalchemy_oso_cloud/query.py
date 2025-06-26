import sqlalchemy.orm
from sqlalchemy.orm import with_loader_criteria, Mapper
from sqlalchemy import text, inspect, select
from oso_cloud import Value
from typing import TypeVar, Self
from .oso import get_oso

T = TypeVar("T")

class Query(sqlalchemy.orm.Query[T]):
  def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)
      self.oso = get_oso()

  def authorized_for(self, actor: Value, action: str) -> Self:
    models = self._extract_models()
    self.get_related_models(models)

    options = []

    for model in models:
       options.append(
          with_loader_criteria(
              model, 
              self.create_auth_criteria(actor, action),
              include_aliases=True
          )
       )

    return self.options(*options)


  def get_related_models(self, models):
    """Extract all related models from SQLAlchemy relationships"""
    related_models = []

    for model in models:
        mapper: Mapper = inspect(model)
        for relationship in mapper.relationships:
          related_class = relationship.mapper.class_
          related_models.append(related_class)
    
    print(f"Related models for {model.__name__}: {[cls.__name__ for cls in related_models]}")
    return related_models
  
  def _extract_models(self):
    """Extract all models being queried"""
    models = set()
    
    for desc in self.column_descriptions:
        print(f"desc: {desc}")
        print(f"desc['entity']: {desc['entity']}")
        if desc['entity'] is not None:
            models.add(desc['entity'])
    return list(models)
  


  def create_auth_criteria(self, actor, action):
    """Factory function to create auth criteria lambda"""
    oso = self.oso
    print(f"Creating auth criteria for actor: {actor}, action: {action}")
    
    def auth_criteria(cls, oso=oso, actor=actor, action=action):
        sql_filter = oso.list_local(
            actor=actor,
            action=action,
            resource_type=cls.__name__.lower(),
            column=f"{cls.__tablename__}.id"
        )
        auth_subquery = select(cls.id).where(text(sql_filter))
        print (f"Auth subquery for {cls.__name__}: {auth_subquery}")
        return cls.id.in_(auth_subquery)
    
    # Mark this lambda as not tracking closure variables
    auth_criteria.__closure_track_closure_variables__ = False
    return auth_criteria