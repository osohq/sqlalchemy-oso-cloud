import sqlalchemy.orm
from sqlalchemy import text
from oso_cloud import Value
from typing import TypeVar
from .oso import get_oso

T = TypeVar("T")
Self = TypeVar("Self", bound="Query")

class Query(sqlalchemy.orm.Query[T]):
  """
  An extension of [`sqlalchemy.orm.Query`](https://docs.sqlalchemy.org/orm/queryguide/query.html#sqlalchemy%2Eorm%2EQuery)
  that adds support for authorization.
  """
  def authorized_for(self: Self, actor: Value, action: str) -> Self:
    """
    Filter the query to only include resources that the given actor is authorized to perform the given action on.

    :param actor: The actor performing the action.
    :param action: The action the actor is performing.

    :return: A new query that includes only the resources that the actor is authorized to perform the action on.
    """
    for col in self._raw_columns:
      print(col)
    authorization_filter = get_oso().list_local(actor, action, "Document", "document.id") # TODO
    return self.where(text(authorization_filter))
