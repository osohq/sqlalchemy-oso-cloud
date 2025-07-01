import sqlalchemy.orm
from sqlalchemy.orm import with_loader_criteria
from sqlalchemy import literal_column, ColumnClause
from oso_cloud import Value
from typing import TypeVar
from .oso import get_oso

T = TypeVar("T")
Self = TypeVar("Self", bound="Query")

#TODO - multiple permissions for multiple main models
class Query(sqlalchemy.orm.Query[T]):
  """
  An extension of [`sqlalchemy.orm.Query`](https://docs.sqlalchemy.org/orm/queryguide/query.html#sqlalchemy%2Eorm%2EQuery)
  that adds support for authorization.
  """
  
  def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)
      self.oso = get_oso()

  def authorized(self: Self, actor: Value, action: str) -> Self:
    """
    Filter the query to only include resources that the given actor is authorized to perform the given action on.

    :param actor: The actor performing the action.
    :param action: The action the actor is performing.

    :return: A new query that includes only the resources that the actor is authorized to perform the action on.
    """
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
        """Create auth criteria"""

        sql_filter = self.oso.list_local(
            actor=actor,
            action=action,
            resource_type=model.__name__,
            column=f"{model.__tablename__}.id"
        )
        criteria: ColumnClause = literal_column(sql_filter)   

        return lambda cls: criteria
