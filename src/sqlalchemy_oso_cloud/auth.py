from typing import TYPE_CHECKING, Callable, List, Optional, Set, Type, Union

from oso_cloud import Value
from sqlalchemy import ColumnClause, literal_column
from sqlalchemy.orm import LoaderCriteriaOption, with_loader_criteria

from .orm import Resource
from .oso import get_oso

if TYPE_CHECKING:
    from .query import Query
    from .select_impl import Select

__all__ = ['authorized', '_apply_authorization_options']


def extract_unique_models(column_descriptions) -> Set[Type]:
    """Extract all models being queried from column descriptions"""
    models = set()
    
    for desc in column_descriptions:
        if desc['entity'] is not None:
            models.add(desc['entity'])
    return models


def create_auth_criteria_for_model(model: Type, actor: Value, action: str) -> Callable:
    """Create authorization criteria for a specific model"""
    oso = get_oso()
    
    sql_filter = oso.list_local(
        actor=actor,
        action=action,
        resource_type=model.__name__,
        column=f"{model.__tablename__}.id"
    )
    
    criteria: ColumnClause = literal_column(sql_filter)
    return lambda cls: criteria


def authorized(actor: Value, action: str, model: Type) -> LoaderCriteriaOption:
    """
    Create authorization options for use with .options()
    
    This function can be used with both Select and Query objects from the SQLAlchemy library:
    
    Examples:
        # With standard SQLAlchemy select
        from sqlalchemy import select
        from sqlalchemy_oso_cloud import authorized

        stmt = select(Document).options(*authorized(user, "read", Document))
        docs = session.execute(stmt).scalars().all()

        # With Query
        docs = session.query(Document).options(*authorized(user, "read", Document)).all()

    :param actor: The actor performing the action
    :param action: The action the actor is performing  
    :param models: The model classes to authorize against
    :return: List of loader criteria options for use with .options()
    """
    
    if not model:
        raise ValueError("Must provide a model to authorize against.")
   
    if not issubclass(model, Resource):
        raise ValueError(f"Model {model.__name__} must inherit from Resource to use authorization")

    
    auth_criteria = create_auth_criteria_for_model(model, actor, action)

    return with_loader_criteria(
            model,
            auth_criteria,
            include_aliases=True
        )
    


def _authorize_all_models(query_obj: Union["Query", "Select"], actor: Value, action: str) -> List[LoaderCriteriaOption]:
    """
    Create authorization options for all Resource models in a query.

    :param query_obj: The query object to extract models from
    :param actor: The actor performing the action
    :param action: The action to authorize
    :return: List of authorization options for all Resource models
    """
    models = extract_unique_models(query_obj.column_descriptions)
    auth_options = []

    for model in models:
        if issubclass(model, Resource):
            auth_options.append(authorized(actor, action, model))

    if not auth_options:
        raise ValueError("No Resource models found in query to authorize")

    return auth_options


def _apply_authorization_options(query_obj: Union["Query",  "Select"], actor: Value, action: str, model: Optional[Type] = None):
    """
    Apply authorization to any query-like object that has column_descriptions and options()
    
    This works with both Select and Query objects.
    """

    if model is not None:
        auth_option = authorized(actor, action, model)
        return query_obj.options(auth_option)
    else:
        auth_options = _authorize_all_models(query_obj, actor, action)
        return query_obj.options(*auth_options)
