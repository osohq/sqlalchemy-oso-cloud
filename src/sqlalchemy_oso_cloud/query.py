import sqlalchemy.orm
from oso_cloud import Value
from typing import TypeVar, Self
from .oso import get_oso
from .auth import _apply_authorization_options

T = TypeVar("T")

# todo - multiple permissions for multiple main models
class Query(sqlalchemy.orm.Query[T]):
  def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)
      self.oso = get_oso()
      self.filter_cache = {}

  def authorized(self, actor: Value, action: str) -> Self:
    return _apply_authorization_options(self, actor, action)
