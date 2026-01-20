"""Helper functions for LLM"""

from __future__ import annotations

import json
import logging
from typing import TypeVar, Type, cast, Any, Dict, Optional

from pydantic import BaseModel

from graph.state import AgentState
from llm.models import get_model, get_model_info, ModelProvider
from utils.progress import progress

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


def call_llm(
    prompt: Any,
    pydantic_model: Type[T],
    agent_name: str | None = None,
    state: AgentState | None = None,
    max_retries: int = 3,
    default_factory=None,
) -> T:
    """
    Makes an LLM call with retry logic, handling both JSON supported and non-JSON supported models.
    """

    # 1. Extract model configuration
    if state and agent_name:
        model_name, model_provider_raw = get_agent_model_config(state, agent_name)
    else:
        # Respect global state if provided, otherwise default to OpenAI
        model_name = state.get("metadata", {}).get("model_name") if state else "gpt-4.1"
        model_provider_raw = state.get("metadata", {}).get("model_provider") if state else ModelProvider.OPENAI.value

    # Normalize model_name and model_provider to str
    model_name_str = str(model_name) if model_name else "gpt-4.1"
    
    # Handle model_provider which can be Enum, str, or None
    if model_provider_raw is None:
        model_provider_str = ModelProvider.OPENAI.value
    elif hasattr(model_provider_raw, "value"):
        model_provider_str = str(getattr(model_provider_raw, "value"))
    else:
        model_provider_str = str(model_provider_raw)

    # 2. Extract API keys
    api_keys = None
    if state:
        request = state.get("metadata", {}).get("request")
        if request and hasattr(request, "api_keys"):
            api_keys = request.api_keys

    model_info = get_model_info(model_name_str, model_provider_str)
    llm = get_model(model_name_str, model_provider_str, api_keys)

    if llm is None:
        logger.error(f"get_model returned None for {model_name_str} from {model_provider_str}")
        if default_factory:
            return default_factory()
        return create_default_response(pydantic_model)

    # 3. Schema Injection (Hardening)
    # Append explicit schema requirements to the prompt to help non-strict models
    schema_fields = list(pydantic_model.model_fields.keys())
    schema_prompt = f"\n\nIMPORTANT: Your output MUST be a JSON object with exactly these keys: {schema_fields}. Do not include any extra keys or conversational text."
    
    if hasattr(prompt, "to_string"):
        prompt_text = prompt.to_string() + schema_prompt
    else:
        prompt_text = str(prompt) + schema_prompt

    # 4. Prepare Model with Structured Output
    if model_info and model_info.has_json_mode():
        llm = llm.with_structured_output(
            pydantic_model,
            method="json_mode",
        )

    # 5. Call the LLM with retries
    for attempt in range(max_retries):
        try:
            # result can be a Pydantic model or a BaseMessage
            result = llm.invoke(prompt_text)

            # Case A: Model already returned parsed Pydantic model (LangChain handled it)
            if isinstance(result, pydantic_model):
                return result

            # Case B: Manual extraction needed (for non-strict or non-JSON support models)
            # Use getattr safely to get content
            content = str(getattr(result, "content", result))
                
            parsed_result = extract_json_from_response(content)
            if parsed_result:
                # Pydantic V2 will handle the map_synonyms validator we added to types.py
                return pydantic_model(**parsed_result)
            
            raise ValueError(f"Could not extract valid JSON from LLM response: {content[:200]}...")

        except Exception as e:
            if agent_name:
                progress.update_status(agent_name, None, f"Error - retry {attempt + 1}/{max_retries}")

            if attempt == max_retries - 1:
                logger.error(f"LLM Failure for {agent_name} after {max_retries} attempts: {e}")
                if default_factory:
                    return default_factory()
                return create_default_response(pydantic_model)

    return create_default_response(pydantic_model)


def create_default_response(model_class: Type[T]) -> T:
    """Creates a safe default response based on the model's fields."""
    default_values = {}
    for field_name, field in model_class.model_fields.items():
        if field.annotation == str:
            default_values[field_name] = "Error in analysis, using default"
        elif field.annotation == float:
            default_values[field_name] = 0.0
        elif field.annotation == int:
            default_values[field_name] = 0
        elif field.annotation is not None and hasattr(field.annotation, "__origin__") and field.annotation.__origin__ == dict:
            default_values[field_name] = {}
        else:
            # For other types (like Literal), try to use the first allowed value
            if field.annotation is not None and hasattr(field.annotation, "__args__"):
                default_values[field_name] = field.annotation.__args__[0]
            else:
                default_values[field_name] = None

    return model_class(**default_values)


def extract_json_from_response(content: str) -> Optional[dict]:
    """Extracts JSON from markdown-formatted response."""
    if not content:
        return None
        
    try:
        # 1. Look for markdown blocks
        json_start = content.find("```json")
        if json_start != -1:
            json_text = content[json_start + 7 :]
            json_end = json_text.find("```")
            if json_end != -1:
                return json.loads(json_text[:json_end].strip())
        
        # 2. Look for raw curly braces
        json_start = content.find("{")
        json_end = content.rfind("}")
        if json_start != -1 and json_end != -1:
            return json.loads(content[json_start : json_end + 1])
            
    except Exception as e:
        logger.warning(f"JSON Extraction Error: {e}")
    return None


def get_agent_model_config(state: AgentState, agent_name: str) -> tuple[str, str]:
    """
    Get model configuration for a specific agent from the state.
    """
    metadata = state.get("metadata", {})
    request = metadata.get("request")

    # 1. Check for Agent-Specific Override
    if request and hasattr(request, "get_agent_model_config"):
        model_name, model_provider = request.get_agent_model_config(agent_name)
        if model_name and model_provider:
            provider_val = str(getattr(model_provider, "value", model_provider))
            return str(model_name), provider_val

    # 2. Check for Global Request Defaults
    model_name = metadata.get("model_name")
    model_provider = metadata.get("model_provider")
    
    if not model_name:
        model_name = "gpt-4.1"
    if not model_provider:
        model_provider = ModelProvider.OPENAI.value
        
    # Convert enum to string if necessary
    provider_str = str(getattr(model_provider, "value", model_provider))

    return str(model_name), provider_str
