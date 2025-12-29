"""
LLM Price Tracker - Normalizer Module

Purpose: Merge data from OpenRouter and LiteLLM into a unified pricing schema.

Input:
- data/current/openrouter.json
- data/current/litellm.json
- data/affiliates.json

Output:
- data/current/prices.json (unified schema)
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Optional
from pydantic import BaseModel, Field


# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CURRENT_DIR = DATA_DIR / "current"


class PricingInfo(BaseModel):
    """Pricing information for a model."""
    input_per_million: float = Field(description="Cost per million input tokens in USD")
    output_per_million: float = Field(description="Cost per million output tokens in USD")
    currency: str = Field(default="USD")


class SourceInfo(BaseModel):
    """Price information from a specific source."""
    price_input: float = Field(description="Input price per million tokens")
    price_output: float = Field(description="Output price per million tokens")
    last_updated: str = Field(description="ISO timestamp of when this was fetched")


class ModelInfo(BaseModel):
    """Complete information about a model."""
    provider: str = Field(description="Provider name (e.g., 'openai', 'anthropic')")
    model_id: str = Field(description="Model identifier")
    display_name: str = Field(description="Human-readable model name")
    pricing: PricingInfo
    context_window: int = Field(default=0, description="Maximum context window size")
    max_output_tokens: int = Field(default=0, description="Maximum output tokens")
    model_type: str = Field(default="chat", description="Model type: chat, image_generation, embedding, audio, etc.")
    supports_vision: bool = Field(default=False)
    supports_function_calling: bool = Field(default=False)
    supports_streaming: bool = Field(default=True)
    category: str = Field(default="general", description="Model category")
    sources: dict[str, SourceInfo] = Field(default_factory=dict)
    affiliate_links: dict[str, str] = Field(default_factory=dict)


class ProviderInfo(BaseModel):
    """Information about a provider."""
    name: str
    website: str
    pricing_page: str
    affiliate_link: str


class PricesSchema(BaseModel):
    """Root schema for prices.json."""
    generated_at: str
    models: dict[str, ModelInfo]
    providers: dict[str, ProviderInfo]
    metadata: dict[str, Any]


def load_json(filepath: Path) -> dict[str, Any]:
    """
    Load a JSON file and return its contents.
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        dict: Parsed JSON data
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file contains invalid JSON
    """
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {filepath}: {e}") from e


def save_json(filepath: Path, data: Any) -> None:
    """Save data to a JSON file with pretty formatting."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved: {filepath}")


def extract_provider(model_id: str) -> str:
    """
    Extract provider name from model ID.
    
    Examples:
        "openai/gpt-4o" -> "openai"
        "anthropic/claude-3-opus" -> "anthropic"
        "gpt-4" -> "openai" (inferred)
    """
    if "/" in model_id:
        return model_id.split("/")[0].lower()
    
    # Infer provider from model name prefix
    model_lower = model_id.lower()
    if model_lower.startswith(("gpt-", "o1-", "davinci", "curie", "babbage", "ada")):
        return "openai"
    elif model_lower.startswith("claude"):
        return "anthropic"
    elif model_lower.startswith("gemini"):
        return "google"
    elif model_lower.startswith(("mistral", "mixtral", "codestral")):
        return "mistral"
    elif model_lower.startswith("llama"):
        return "meta"
    elif model_lower.startswith("deepseek"):
        return "deepseek"
    elif model_lower.startswith("command"):
        return "cohere"
    
    return "unknown"


def create_display_name(model_id: str) -> str:
    """
    Create a human-readable display name from model ID.
    
    Examples:
        "openai/gpt-4o" -> "GPT-4o"
        "anthropic/claude-3-opus-20240229" -> "Claude 3 Opus"
    """
    # Remove provider prefix
    name = model_id.split("/")[-1] if "/" in model_id else model_id
    
    # Remove date suffixes
    import re
    name = re.sub(r"-\d{8}$", "", name)
    name = re.sub(r":\d{8}$", "", name)
    
    # Clean up common patterns
    name = name.replace("-", " ").replace("_", " ")
    
    # Title case with special handling
    words = name.split()
    result = []
    for word in words:
        if word.lower() in ("gpt", "llm", "ai"):
            result.append(word.upper())
        elif word.lower().startswith("gpt"):
            result.append("GPT" + word[3:])
        else:
            result.append(word.capitalize())
    
    return " ".join(result)


def categorize_model(model_id: str, context_window: int, input_price: float) -> str:
    """
    Categorize a model based on its characteristics.
    
    Categories:
    - flagship: High-end, most capable models
    - standard: Good balance of capability and cost
    - budget: Cost-effective models
    - code: Specialized for code generation
    - embedding: Embedding models
    """
    model_lower = model_id.lower()
    
    # Check for embedding models
    if "embed" in model_lower:
        return "embedding"
    
    # Check for code-specialized models
    if any(x in model_lower for x in ["codestral", "code-", "coder", "starcoder", "codellama"]):
        return "code"
    
    # Check for flagship models
    flagship_patterns = [
        "gpt-4o", "gpt-4-turbo", "gpt-4-32k",
        "claude-3-opus", "claude-3.5-sonnet", "claude-4",
        "gemini-1.5-pro", "gemini-ultra",
        "o1-preview", "o1-pro"
    ]
    if any(pattern in model_lower for pattern in flagship_patterns):
        return "flagship"
    
    # Categorize by price
    if input_price > 5.0:
        return "flagship"
    elif input_price > 0.5:
        return "standard"
    else:
        return "budget"


def normalize_openrouter(raw_data: dict[str, Any], fetched_at: str) -> dict[str, ModelInfo]:
    """
    Transform OpenRouter format to unified schema.
    
    OpenRouter format:
    {
        "id": "openai/gpt-4o",
        "name": "GPT-4o",
        "pricing": {"prompt": "0.000005", "completion": "0.000015"},
        "context_length": 128000,
        "top_provider": {"max_completion_tokens": 16384}
    }
    
    Args:
        raw_data: Raw OpenRouter API response
        fetched_at: ISO timestamp of when data was fetched
        
    Returns:
        dict: Normalized models keyed by model_id
    """
    models: dict[str, ModelInfo] = {}
    
    data_list = raw_data.get("data", [])
    if not isinstance(data_list, list):
        print(f"⚠ OpenRouter data is not a list, got {type(data_list).__name__}")
        return models
    
    for item in data_list:
        try:
            model_id = item.get("id", "")
            if not model_id:
                continue
            
            # Parse pricing (OpenRouter uses cost per token as string)
            pricing_data = item.get("pricing", {})
            prompt_cost = float(pricing_data.get("prompt", 0) or 0)
            completion_cost = float(pricing_data.get("completion", 0) or 0)
            
            # Convert from per-token to per-million
            input_per_million = prompt_cost * 1_000_000
            output_per_million = completion_cost * 1_000_000
            
            # Get context and output limits
            context_window = int(item.get("context_length", 0) or 0)
            top_provider = item.get("top_provider", {}) or {}
            max_output = int(top_provider.get("max_completion_tokens", 0) or 0)
            
            # Determine capabilities
            architecture = item.get("architecture", {}) or {}
            modality = architecture.get("modality", "")
            output_modalities = architecture.get("output_modalities", [])
            
            # Determine model type from modality
            if "image" in (output_modalities or []):
                model_type = "image_generation"
            elif modality and "text" in modality.lower():
                model_type = "chat"
            else:
                model_type = "chat"  # Default for OpenRouter
            
            provider = extract_provider(model_id)
            
            model_info = ModelInfo(
                provider=provider,
                model_id=model_id,
                display_name=item.get("name", create_display_name(model_id)),
                pricing=PricingInfo(
                    input_per_million=round(input_per_million, 4),
                    output_per_million=round(output_per_million, 4),
                    currency="USD"
                ),
                context_window=context_window,
                max_output_tokens=max_output,
                model_type=model_type,
                supports_vision="image" in modality.lower() if modality else False,
                supports_function_calling=True,  # Most models on OpenRouter support this
                supports_streaming=True,
                category=categorize_model(model_id, context_window, input_per_million),
                sources={
                    "openrouter": SourceInfo(
                        price_input=round(input_per_million, 4),
                        price_output=round(output_per_million, 4),
                        last_updated=fetched_at
                    )
                }
            )
            
            models[model_id] = model_info
            
        except (ValueError, TypeError, KeyError) as e:
            print(f"⚠ Skipping model {item.get('id', 'unknown')}: {e}")
            continue
    
    return models


def normalize_litellm(raw_data: dict[str, Any], fetched_at: str) -> dict[str, ModelInfo]:
    """
    Transform LiteLLM format to unified schema.
    
    LiteLLM format (per model entry):
    {
        "max_tokens": 4096,
        "max_input_tokens": 128000,
        "input_cost_per_token": 0.00001,
        "output_cost_per_token": 0.00003,
        "litellm_provider": "openai"
    }
    
    Args:
        raw_data: Raw LiteLLM pricing data
        fetched_at: ISO timestamp
        
    Returns:
        dict: Normalized models keyed by model_id
    """
    models: dict[str, ModelInfo] = {}
    
    data = raw_data.get("data", {})
    if not isinstance(data, dict):
        print(f"⚠ LiteLLM data is not a dict, got {type(data).__name__}")
        return models
    
    for model_key, model_data in data.items():
        try:
            if not isinstance(model_data, dict):
                continue
            
            # Skip sample/test entries
            if model_key.startswith("sample_spec"):
                continue
            
            # Get pricing (LiteLLM uses cost per token)
            input_cost = float(model_data.get("input_cost_per_token", 0) or 0)
            output_cost = float(model_data.get("output_cost_per_token", 0) or 0)
            
            # Convert to per-million
            input_per_million = input_cost * 1_000_000
            output_per_million = output_cost * 1_000_000
            
            # Skip models with no pricing data
            if input_per_million == 0 and output_per_million == 0:
                continue
            
            # Get context limits
            max_input = int(model_data.get("max_input_tokens", 0) or 0)
            max_output = int(model_data.get("max_tokens", 0) or model_data.get("max_output_tokens", 0) or 0)
            
            # LiteLLM uses litellm_provider or we extract from key
            provider = model_data.get("litellm_provider", "") or extract_provider(model_key)
            
            # Get model type from LiteLLM mode field
            mode = model_data.get("mode", "chat")
            # Normalize mode names
            if mode in ("chat", "completion", "responses"):
                model_type = "chat"
            elif mode in ("image_generation", "image_edit"):
                model_type = "image"
            elif mode == "embedding":
                model_type = "embedding"
            elif mode in ("audio_transcription", "audio_speech"):
                model_type = "audio"
            elif mode == "video_generation":
                model_type = "video"
            elif mode == "rerank":
                model_type = "rerank"
            else:
                model_type = mode if mode else "chat"
            
            # Determine capabilities
            supports_vision = model_data.get("supports_vision", False) or False
            supports_fc = model_data.get("supports_function_calling", False) or False
            
            model_info = ModelInfo(
                provider=provider.lower() if provider else extract_provider(model_key),
                model_id=model_key,
                display_name=create_display_name(model_key),
                pricing=PricingInfo(
                    input_per_million=round(input_per_million, 4),
                    output_per_million=round(output_per_million, 4),
                    currency="USD"
                ),
                context_window=max_input,
                max_output_tokens=max_output,
                model_type=model_type,
                supports_vision=supports_vision,
                supports_function_calling=supports_fc,
                supports_streaming=True,
                category=categorize_model(model_key, max_input, input_per_million),
                sources={
                    "litellm": SourceInfo(
                        price_input=round(input_per_million, 4),
                        price_output=round(output_per_million, 4),
                        last_updated=fetched_at
                    )
                }
            )
            
            models[model_key] = model_info
            
        except (ValueError, TypeError, KeyError) as e:
            print(f"⚠ Skipping LiteLLM model {model_key}: {e}")
            continue
    
    return models


def merge_sources(
    openrouter_models: dict[str, ModelInfo],
    litellm_models: dict[str, ModelInfo]
) -> dict[str, ModelInfo]:
    """
    Merge models from both sources.
    
    Strategy:
    - If model exists in both, merge sources and use OpenRouter for capabilities
    - OpenRouter is considered more accurate for capabilities (vision, function calling)
    - Both price sources are preserved for comparison
    
    Args:
        openrouter_models: Models from OpenRouter
        litellm_models: Models from LiteLLM
        
    Returns:
        dict: Merged models
    """
    merged: dict[str, ModelInfo] = {}
    
    # Start with OpenRouter models (primary source)
    for model_id, model in openrouter_models.items():
        merged[model_id] = model
    
    # Add/merge LiteLLM models
    for model_id, litellm_model in litellm_models.items():
        if model_id in merged:
            # Model exists in OpenRouter - add LiteLLM as additional source
            existing = merged[model_id]
            existing.sources["litellm"] = litellm_model.sources.get("litellm")
        else:
            # New model from LiteLLM
            merged[model_id] = litellm_model
    
    return merged


def inject_affiliates(
    models: dict[str, ModelInfo],
    affiliates_data: dict[str, Any]
) -> dict[str, ModelInfo]:
    """
    Add affiliate links to each model based on provider.
    
    Args:
        models: Dictionary of models
        affiliates_data: Affiliate configuration
        
    Returns:
        dict: Models with affiliate links added
    """
    providers = affiliates_data.get("providers", {})
    
    for model_id, model in models.items():
        provider = model.provider.lower()
        
        if provider in providers:
            provider_info = providers[provider]
            model.affiliate_links = {
                provider: provider_info.get("affiliate_link", ""),
                "openrouter": providers.get("openrouter", {}).get("affiliate_link", "")
            }
    
    return models


def build_providers_dict(affiliates_data: dict[str, Any]) -> dict[str, ProviderInfo]:
    """Build provider information dictionary from affiliates data."""
    providers: dict[str, ProviderInfo] = {}
    
    for provider_id, data in affiliates_data.get("providers", {}).items():
        providers[provider_id] = ProviderInfo(
            name=data.get("name", provider_id.title()),
            website=data.get("website", ""),
            pricing_page=data.get("pricing_page", ""),
            affiliate_link=data.get("affiliate_link", "")
        )
    
    return providers


def main() -> None:
    """
    Main entry point for the normalizer.
    
    Workflow:
    1. Load raw data from OpenRouter and LiteLLM
    2. Normalize each source to unified schema
    3. Merge sources
    4. Inject affiliate links
    5. Save to prices.json
    """
    print("=" * 60)
    print("LLM Price Tracker - Normalizer")
    print(f"Started at: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)
    
    # Load raw data
    print("\n📂 Loading raw data...")
    
    openrouter_raw = load_json(CURRENT_DIR / "openrouter.json")
    print(f"✓ Loaded OpenRouter: {openrouter_raw.get('model_count', 0)} models")
    
    litellm_raw = load_json(CURRENT_DIR / "litellm.json")
    print(f"✓ Loaded LiteLLM: {litellm_raw.get('model_count', 0)} entries")
    
    affiliates = load_json(DATA_DIR / "affiliates.json")
    print(f"✓ Loaded affiliates configuration")
    
    # Normalize each source
    print("\n🔄 Normalizing data...")
    
    openrouter_fetched_at = openrouter_raw.get("fetched_at", datetime.now(timezone.utc).isoformat())
    openrouter_models = normalize_openrouter(openrouter_raw, openrouter_fetched_at)
    print(f"✓ Normalized OpenRouter: {len(openrouter_models)} valid models")
    
    litellm_fetched_at = litellm_raw.get("fetched_at", datetime.now(timezone.utc).isoformat())
    litellm_models = normalize_litellm(litellm_raw, litellm_fetched_at)
    print(f"✓ Normalized LiteLLM: {len(litellm_models)} valid models")
    
    # Merge sources
    print("\n🔀 Merging sources...")
    merged_models = merge_sources(openrouter_models, litellm_models)
    print(f"✓ Merged: {len(merged_models)} total models")
    
    # Inject affiliate links
    print("\n💰 Injecting affiliate links...")
    final_models = inject_affiliates(merged_models, affiliates)
    
    # Build final schema
    now = datetime.now(timezone.utc).isoformat()
    providers = build_providers_dict(affiliates)
    
    # Count models by category
    categories: dict[str, int] = {}
    for model in final_models.values():
        cat = model.category
        categories[cat] = categories.get(cat, 0) + 1
    
    # Convert Pydantic models to dicts for JSON serialization
    models_dict = {k: v.model_dump() for k, v in final_models.items()}
    providers_dict = {k: v.model_dump() for k, v in providers.items()}
    
    prices_data = {
        "generated_at": now,
        "models": models_dict,
        "providers": providers_dict,
        "metadata": {
            "total_models": len(final_models),
            "sources": ["openrouter", "litellm"],
            "last_scrape": now,
            "categories": categories
        }
    }
    
    # Save result
    print("\n💾 Saving normalized data...")
    save_json(CURRENT_DIR / "prices.json", prices_data)
    
    print("\n" + "=" * 60)
    print("✅ Normalization completed successfully!")
    print(f"   Total models: {len(final_models)}")
    print(f"   Categories: {categories}")
    print("=" * 60)


if __name__ == "__main__":
    main()
