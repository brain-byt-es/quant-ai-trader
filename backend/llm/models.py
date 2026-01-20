import json
import os
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple, Union, Any, Dict

from langchain_anthropic import ChatAnthropic
from langchain_deepseek import ChatDeepSeek
from langchain_gigachat import GigaChat
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain_xai import ChatXAI
from pydantic import BaseModel, SecretStr

from utils.signature import validate_and_filter_kwargs


class ModelProvider(str, Enum):
    """Enum for supported LLM providers"""

    ALIBABA = "Alibaba"
    ANTHROPIC = "Anthropic"
    DEEPSEEK = "DeepSeek"
    GOOGLE = "Google"
    GROQ = "Groq"
    META = "Meta"
    MISTRAL = "Mistral"
    OPENAI = "OpenAI"
    OLLAMA = "Ollama"
    OPENROUTER = "OpenRouter"
    GIGACHAT = "GigaChat"
    AZURE_OPENAI = "Azure OpenAI"
    XAI = "xAI"


class LLMModel(BaseModel):
    """Represents an LLM model configuration"""

    display_name: str
    model_name: str
    provider: ModelProvider

    def to_choice_tuple(self) -> Tuple[str, str, str]:
        """Convert to format needed for questionary choices"""
        return (self.display_name, self.model_name, self.provider.value)

    def is_custom(self) -> bool:
        """Check if the model is a Gemini model"""
        return self.model_name == "-"

    def has_json_mode(self) -> bool:
        """Check if the model supports JSON mode"""
        if self.is_deepseek() or self.is_gemini():
            return False
        # Only certain Ollama models support JSON mode
        if self.is_ollama():
            return "llama3" in self.model_name or "neural-chat" in self.model_name
        # OpenRouter models generally support JSON mode
        if self.provider == ModelProvider.OPENROUTER:
            return True
        return True

    def is_deepseek(self) -> bool:
        """Check if the model is a DeepSeek model"""
        return self.model_name.startswith("deepseek")

    def is_gemini(self) -> bool:
        """Check if the model is a Gemini model"""
        return self.model_name.startswith("gemini")

    def is_ollama(self) -> bool:
        """Check if the model is an Ollama model"""
        return self.provider == ModelProvider.OLLAMA


# Load models from JSON file
def load_models_from_json(json_path: str) -> List[LLMModel]:
    """Load models from a JSON file"""
    with open(json_path, "r") as f:
        models_data = json.load(f)

    models = []
    for model_data in models_data:
        # Convert string provider to ModelProvider enum
        provider_enum = ModelProvider(model_data["provider"])
        models.append(LLMModel(display_name=model_data["display_name"], model_name=model_data["model_name"], provider=provider_enum))
    return models


# Get the path to the JSON files
current_dir = Path(__file__).parent
models_json_path = current_dir / "api_models.json"
ollama_models_json_path = current_dir / "ollama_models.json"

# Load available models from JSON
AVAILABLE_MODELS = load_models_from_json(str(models_json_path))

# Load Ollama models from JSON
OLLAMA_MODELS = load_models_from_json(str(ollama_models_json_path))

# Create LLM_ORDER in the format expected by the UI
LLM_ORDER = [model.to_choice_tuple() for model in AVAILABLE_MODELS]

# Create Ollama LLM_ORDER separately
OLLAMA_LLM_ORDER = [model.to_choice_tuple() for model in OLLAMA_MODELS]


def get_model_info(model_name: str, model_provider: str) -> Optional[LLMModel]:
    """Get model information by model_name"""
    all_models = AVAILABLE_MODELS + OLLAMA_MODELS
    # Normalize model_provider if it's a string like "OPENAI"
    normalized_provider = model_provider
    if isinstance(model_provider, str):
        for p in ModelProvider:
            if p.value.lower() == model_provider.lower() or p.name.lower() == model_provider.lower():
                normalized_provider = p.value
                break

    return next((model for model in all_models if model.model_name == model_name and model.provider == normalized_provider), None)


def find_model_by_name(model_name: str) -> Optional[LLMModel]:
    """Find a model by its name across all available models."""
    all_models = AVAILABLE_MODELS + OLLAMA_MODELS
    return next((model for model in all_models if model.model_name == model_name), None)


def get_models_list():
    """Get the list of models for API responses."""
    return [{"display_name": model.display_name, "model_name": model.model_name, "provider": model.provider.value} for model in AVAILABLE_MODELS]


def get_model(model_name: str, model_provider: Union[ModelProvider, str], api_keys: Optional[dict] = None) -> Optional[Union[ChatOpenAI, ChatGroq, ChatOllama, GigaChat, ChatAnthropic, ChatDeepSeek, ChatGoogleGenerativeAI, ChatXAI, AzureChatOpenAI]]:
    # Normalize model_provider to ModelProvider enum if it's a string
    if isinstance(model_provider, str):
        try:
            # Try to match by value (e.g., "OpenAI")
            model_provider = ModelProvider(model_provider)
        except ValueError:
            # Try to match by name (e.g., "OPENAI") or case-insensitive value
            found = False
            for p in ModelProvider:
                if p.name.lower() == model_provider.lower() or p.value.lower() == model_provider.lower():
                    model_provider = p
                    found = True
                    break
            if not found:
                print(f"Warning: Unknown model provider '{model_provider}'. Falling back to OpenAI.")
                model_provider = ModelProvider.OPENAI

    # Factory configuration
    kwargs: Dict[str, Any] = {}
    provider_cls: Any = None

    if model_provider == ModelProvider.GROQ:
        api_key = (api_keys or {}).get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Groq API key not found.")
        provider_cls = ChatGroq
        kwargs = {"model_name": model_name, "api_key": SecretStr(api_key), "timeout": None}
        
    elif model_provider == ModelProvider.OPENAI:
        api_key = (api_keys or {}).get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not found.")
        provider_cls = ChatOpenAI
        kwargs = {"model": model_name, "api_key": SecretStr(api_key), "base_url": os.getenv("OPENAI_API_BASE")}
        
    elif model_provider == ModelProvider.ANTHROPIC:
        api_key = (api_keys or {}).get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Anthropic API key not found.")
        provider_cls = ChatAnthropic
        kwargs = {"model_name": model_name, "api_key": SecretStr(api_key)}
        
    elif model_provider == ModelProvider.DEEPSEEK:
        api_key = (api_keys or {}).get("DEEPSEEK_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DeepSeek API key not found.")
        provider_cls = ChatDeepSeek
        kwargs = {"model_name": model_name, "api_key": SecretStr(api_key)}
        
    elif model_provider == ModelProvider.GOOGLE:
        api_key = (api_keys or {}).get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Google API key not found.")
        provider_cls = ChatGoogleGenerativeAI
        kwargs = {"model": model_name, "api_key": SecretStr(api_key)}
        
    elif model_provider == ModelProvider.OLLAMA:
        ollama_host = os.getenv("OLLAMA_HOST", "localhost")
        provider_cls = ChatOllama
        kwargs = {"model": model_name, "base_url": os.getenv("OLLAMA_BASE_URL", f"http://{ollama_host}:11434")}
        
    elif model_provider == ModelProvider.OPENROUTER:
        api_key = (api_keys or {}).get("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OpenRouter API key not found.")
        provider_cls = ChatOpenAI
        kwargs = {
            "model": model_name,
            "api_key": SecretStr(api_key),
            "base_url": "https://openrouter.ai/api/v1",
            "model_kwargs": {
                "extra_headers": {
                    "HTTP-Referer": os.getenv("YOUR_SITE_URL", "https://github.com/virattt/ai-hedge-fund"),
                    "X-Title": os.getenv("YOUR_SITE_NAME", "AI Hedge Fund"),
                }
            },
        }
    elif model_provider == ModelProvider.XAI:
        api_key = (api_keys or {}).get("XAI_API_KEY") or os.getenv("XAI_API_KEY")
        if not api_key:
            raise ValueError("xAI API key not found.")
        provider_cls = ChatXAI
        kwargs = {"model": model_name, "api_key": SecretStr(api_key)}
        
    elif model_provider == ModelProvider.GIGACHAT:
        provider_cls = GigaChat
        api_key = (api_keys or {}).get("GIGACHAT_API_KEY") or os.getenv("GIGACHAT_API_KEY") or os.getenv("GIGACHAT_CREDENTIALS")
        if os.getenv("GIGACHAT_USER") or os.getenv("GIGACHAT_PASSWORD"):
            kwargs = {"model": model_name}
        elif api_key:
            kwargs = {"credentials": api_key, "model": model_name}
        else:
            raise ValueError("GigaChat credentials not found.")
            
    elif model_provider == ModelProvider.AZURE_OPENAI:
        provider_cls = AzureChatOpenAI
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Azure OpenAI configuration not found.")
        kwargs = {
            "azure_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
            "azure_deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            "api_key": SecretStr(api_key),
            "api_version": "2024-10-21"
        }

    if provider_cls:
        # Use signature introspection to safely handle version drift
        safe_kwargs = validate_and_filter_kwargs(provider_cls, kwargs)
        return provider_cls(**safe_kwargs)
    
    return None