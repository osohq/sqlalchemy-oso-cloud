import sqlalchemy.orm
from sqlalchemy.orm import with_loader_criteria, Mapper
from sqlalchemy import text, inspect, select, literal_column, ColumnClause
from oso_cloud import Value
from typing import Type, TypeVar, Optional

from .auth import _apply_authorization_options
from .oso import get_oso
from .orm import Resource

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

  def authorized(self: Self, actor: Value, action: str, model: Optional[Type] = None ) -> Self:
    """
    Filter the query to only include resources that the given actor is authorized to perform the given action on.

    :param actor: The actor performing the action.
    :param action: The action the actor is performing.

    :return: A new query that includes only the resources that the actor is authorized to perform the action on.
    """
    return _apply_authorization_options(self, actor, action, model)
  
