"""
Utilities for [declaratively mapping](https://docs.sqlalchemy.org/en/20/orm/mapping_styles.html#orm-declarative-mapping)
[authorization data](https://www.osohq.com/docs/authorization-data) in your ORM models.
"""
import inspect

from typing import Callable, Any, Optional, Dict
from typing_extensions import ParamSpec, TypeVar
from functools import wraps

from sqlalchemy.orm import MappedColumn, Relationship, mapped_column, relationship
from typing import Union

class Resource:
  """
  A mixin to indicate that an ORM model corresponds to an Oso resource.
  """
  pass

_RELATION_INFO_KEY = "_oso.relation"
_ATTRIBUTE_INFO_KEY = "_oso.attribute"
_REMOTE_RELATION_INFO_KEY = "_oso.remote_relation"

P = ParamSpec('P')
T = TypeVar('T')

def wrap(func: Callable[P, Any]) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Wrap a SQLAlchemy function in a type-safe way."""
    def decorator(wrapper: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapped(*args: P.args, **kwargs: P.kwargs) -> T:
            return wrapper(*args, **kwargs)
        return wrapped
    return decorator

F = TypeVar('F', bound=Callable[..., Any])

def wrap_with_signature(
    wrapped_func: Callable,
    extra_params: Optional[Dict[str, Dict[str, Any]]] = None
):
    """
    Decorator that copies signature from wrapped_func and optionally adds extra parameters.
    
    Args:
        wrapped_func: The function whose signature to copy
        extra_params: Dict of {param_name: {'annotation': type, 'default': value}}
    """
    def decorator(wrapper_func: F) -> F:
        # Get the original signature
        sig = inspect.signature(wrapped_func)
        params = list(sig.parameters.values())
        
        # Add extra parameters as keyword-only
        if extra_params:
            for name, info in extra_params.items():
                param = inspect.Parameter(
                    name,
                    inspect.Parameter.KEYWORD_ONLY,
                    default=info.get('default', inspect.Parameter.empty),
                    annotation=info.get('annotation', inspect.Parameter.empty)
                )
                params.append(param)
        
        # Create new signature
        new_sig = sig.replace(parameters=params)
        
        # Apply to wrapper function
        wrapper_func.__signature__ = new_sig
        wrapper_func.__annotations__ = getattr(wrapped_func, '__annotations__', {})
        
        # Add extra param annotations
        if extra_params:
            for name, info in extra_params.items():
                if 'annotation' in info:
                    wrapper_func.__annotations__[name] = info['annotation']
        
        wrapper_func.__name__ = wrapped_func.__name__
        wrapper_func.__doc__ = wrapped_func.__doc__
        wrapper_func.__module__ = wrapped_func.__module__
        
        return wrapper_func
    
    return decorator

@wrap_with_signature(relationship)
def relation(*args, **kwargs) -> Relationship:
  """
  A wrapper around [`sqlalchemy.orm.relationship`](https://docs.sqlalchemy.org/en/20/orm/relationship_api.html#sqlalchemy.orm.relationship)
  that indicates that the relationship corresponds to `has_relation` facts in Oso with the following three arguments:
  1. the resource this relationship is declared on,
  2. the name of this relationship, and
  3. the resource that the relationship points to.

  Accepts all of the same arguments as [`sqlalchemy.orm.relationship`](https://docs.sqlalchemy.org/en/20/orm/relationship_api.html#sqlalchemy.orm.relationship).
  """
  rel = relationship(*args, **kwargs)
  rel.info[_RELATION_INFO_KEY] = None
  return rel

@wrap(mapped_column)
def attribute(*args, **kwargs) -> MappedColumn:
  """
  A wrapper around [`sqlalchemy.orm.mapped_column`](https://docs.sqlalchemy.org/en/20/orm/mapping_api.html#sqlalchemy.orm.mapped_column)
  that indicates that the attribute corresponds to `has_{attribute_name}` facts in Oso with the following two arguments:
  1. the resource this attribute is declared on, and
  2. the attribute value.

  Accepts all of the same arguments as [`sqlalchemy.orm.mapped_column`](https://docs.sqlalchemy.org/en/20/orm/mapping_api.html#sqlalchemy.orm.mapped_column).
  """
  col = mapped_column(*args, **kwargs)
  col.column.info[_ATTRIBUTE_INFO_KEY] = None
  return col

def remote_relation(remote_resource_name: str, remote_relation_key: Union[str, None] = None, *args, **kwargs) -> MappedColumn:
  """
  A wrapper around [`sqlalchemy.orm.mapped_column`](https://docs.sqlalchemy.org/en/20/orm/mapping_api.html#sqlalchemy.orm.mapped_column)
  that indicates that the attribute corresponds to `has_relation` facts (to a resource not defined in the local database) in Oso with the following two arguments:
  1. the resource this attribute is declared on, and
  2. the name of this relationship, and
  3. the resource that the relationship points to.

  Note: this is not a [`sqlalchemy.orm.relationship`](https://docs.sqlalchemy.org/en/20/orm/relationship_api.html#sqlalchemy.orm.relationship).

  Accepts all of the same arguments as [`sqlalchemy.orm.mapped_column`](https://docs.sqlalchemy.org/en/20/orm/mapping_api.html#sqlalchemy.orm.mapped_column).
  Also accepts the following additional arguments:
  :param remote_resource_name: the name of the remote resource
  :param remote_relation_key: (optional) the name of the relation on the remote resource. If not provided, the name of the relation will be inferred from the name of the column.
  """
  col = mapped_column(*args, **kwargs)
  col.column.info[_REMOTE_RELATION_INFO_KEY] = (remote_resource_name, remote_relation_key)
  return col