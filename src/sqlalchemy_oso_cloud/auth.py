from sqlalchemy.orm import with_loader_criteria
from sqlalchemy import literal_column, ColumnClause
from oso_cloud import Value
from typing import Set, Type, Callable
from .orm import Resource
from .oso import get_oso

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


def authorized(actor: Value, action: str, *models: Type) -> list:
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
    
    if len(models) > 1:
        raise ValueError("Currently only single model authorization is supported.")
    if len(models) == 0:
        raise ValueError("Must provide a model to authorize against.")

    options = []
    for model in models:
        if not issubclass(model, Resource):
            continue
        auth_criteria = create_auth_criteria_for_model(model, actor, action)
        options.append(
            with_loader_criteria(
                model,
                auth_criteria,
                include_aliases=True
            )
        )
    return options


def _apply_authorization_options(query_obj, actor: Value, action: str):
    """
    Apply authorization to any query-like object that has column_descriptions and options()
    
    This works with both Select and Query objects.
    """
    models = extract_unique_models(query_obj.column_descriptions)
    auth_options = authorized(actor, action, *models)
    return query_obj.options(*auth_options)
