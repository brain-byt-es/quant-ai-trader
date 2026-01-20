import inspect
import logging
from typing import Any, Dict, Type

logger = logging.getLogger(__name__)

def validate_and_filter_kwargs(cls: Type, kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Introspects a class constructor and filters kwargs to match its signature.
    Prevents runtime crashes due to library version drift.
    """
    signature = inspect.signature(cls.__init__)
    parameters = signature.parameters
    
    # Check if the class accepts arbitrary kwargs (**kwargs)
    has_var_kwargs = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in parameters.values())
    
    if has_var_kwargs:
        return kwargs

    filtered_kwargs = {}
    dropped_args = []
    
    for key, value in kwargs.items():
        if key in parameters:
            filtered_kwargs[key] = value
        else:
            dropped_args.append(key)
            
    if dropped_args:
        logger.warning(
            f"Provider class {cls.__name__} does not support arguments: {dropped_args}. "
            "These have been dropped to prevent a runtime crash. check your library versions."
        )
        
    return filtered_kwargs
