import sqlalchemy.orm
from sqlalchemy import text
from oso_cloud import Value
from typing import TypeVar, Self
from .oso import get_oso

T = TypeVar("T")

class Query(sqlalchemy.orm.Query[T]):
  def authorized_for(self, actor: Value, action: str) -> Self:
    for col in self._raw_columns:
      print(col)
    authorization_filter = get_oso().list_local(actor, action, "Document", "document.id") # TODO
    print("authorization_filter", authorization_filter)
    return self.where(text(authorization_filter))
