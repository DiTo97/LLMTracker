"""
LLM Price Tracker - Normalizer Module (tokenprice fork)

Purpose: Merge data from OpenRouter and LiteLLM into a unified pricing schema.

This fork extends the original LLMTracker to include cache pricing fields:
- cache_read_per_million: Cost for cache hits (reading from cache)
- cache_creation_per_million: Cost for cache misses (writing to cache)

Input:
- data/current/openrouter.json
- data/current/litellm.json

Output:
- data/current/prices.json (unified schema)

Credits: Original implementation from https://github.com/MrUnreal/LLMTracker
"""

import json
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Optional
from pydantic import BaseModel, Field


# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CURRENT_DIR = DATA_DIR / "current"


class PricingInfo(BaseModel):
    """Pricing information for a model, including cache pricing."""

    input_per_million: float = Field(
        description="Cost per million input tokens in USD"
    )
    output_per_million: float = Field(
        description="Cost per million output tokens in USD"
    )
    cache_read_per_million: Optional[float] = Field(
        default=None, description="Cost per million cached input tokens (cache hit)"
    )
    cache_creation_per_million: Optional[float] = Field(
        default=None,
        description="Cost per million cached input tokens (cache write/miss)",
    )
    currency: str = Field(default="USD")


class SourceInfo(BaseModel):
    """Price information from a specific source."""

    price_input: float = Field(description="Input price per million tokens")
    price_output: float = Field(description="Output price per million tokens")
    price_cache_read: Optional[float] = Field(
        default=None, description="Cache read price per million tokens"
    )
    price_cache_creation: Optional[float] = Field(
        default=None, description="Cache creation price per million tokens"
    )
    last_updated: str = Field(description="ISO timestamp of when this was fetched")


class ModelInfo(BaseModel):
    """Complete information about a model."""

    provider: str = Field(description="Provider name (e.g., 'openai', 'anthropic')")
    model_id: str = Field(description="Model identifier")
    display_name: str = Field(description="Human-readable model name")
    pricing: PricingInfo
    context_window: int = Field(default=0, description="Maximum context window size")
    max_output_tokens: int = Field(default=0, description="Maximum output tokens")
    model_type: str = Field(
        default="chat",
        description="Model type: chat, image_generation, embedding, audio, etc.",
    )
    supports_vision: bool = Field(default=False)
    supports_function_calling: bool = Field(default=False)
    supports_streaming: bool = Field(default=True)
    category: str = Field(default="general", description="Model category")
    sources: dict[str, SourceInfo] = Field(default_factory=dict)


class ProviderInfo(BaseModel):
    """Information about a provider."""

    name: str
    website: str
    pricing_page: str


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
    if model_lower.startswith(("gpt-", "o1-", "o3-", "o4-", "davinci", "curie", "babbage", "ada")):
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
    if any(
        x in model_lower
        for x in ["codestral", "code-", "coder", "starcoder", "codellama"]
    ):
        return "code"

    # Check for flagship models
    flagship_patterns = [
        "gpt-4o",
        "gpt-4-turbo",
        "gpt-4-32k",
        "gpt-5",
        "claude-3-opus",
        "claude-3.5-sonnet",
        "claude-4",
        "claude-opus-4",
        "claude-sonnet-4",
        "gemini-1.5-pro",
        "gemini-2",
        "gemini-3",
        "gemini-ultra",
        "o1-preview",
        "o1-pro",
        "o3",
        "o4",
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


def parse_cache_price(value: Any) -> Optional[float]:
    """
    Parse cache price from various formats.

    Args:
        value: Price value (string, float, int, or None)

    Returns:
        float or None: Parsed price or None if not available
    """
    if value is None:
        return None
    try:
        price = float(value)
        return price if price > 0 else None
    except (ValueError, TypeError):
        return None


def normalize_openrouter(
    raw_data: dict[str, Any], fetched_at: str
) -> dict[str, ModelInfo]:
    """
    Transform OpenRouter format to unified schema.

    OpenRouter format:
    {
        "id": "openai/gpt-4o",
        "name": "GPT-4o",
        "pricing": {
            "prompt": "0.000005",
            "completion": "0.000015",
            "input_cache_read": "0.00000125",
            "input_cache_write": "0.000005"
        },
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

            # Parse cache pricing (new fields)
            cache_read_cost = parse_cache_price(pricing_data.get("input_cache_read"))
            cache_write_cost = parse_cache_price(pricing_data.get("input_cache_write"))

            # Convert from per-token to per-million
            input_per_million = prompt_cost * 1_000_000
            output_per_million = completion_cost * 1_000_000
            cache_read_per_million = (
                cache_read_cost * 1_000_000 if cache_read_cost else None
            )
            cache_creation_per_million = (
                cache_write_cost * 1_000_000 if cache_write_cost else None
            )

            # Get context and output limits
            context_window = int(item.get("context_length", 0) or 0)
            top_provider = item.get("top_provider", {}) or {}
            max_output = int(top_provider.get("max_completion_tokens", 0) or 0)

            # Determine capabilities
            architecture = item.get("architecture", {}) or {}
            modality = architecture.get("modality", "")
            output_modalities = architecture.get("output_modalities", [])

            # Determine model type from modality and name patterns
            model_name_lower = model_id.lower()

            # Known image model patterns
            image_patterns = [
                "stable-diffusion",
                "sdxl",
                "flux",
                "dall-e",
                "midjourney",
                "playground-v2",
                "ssd-1b",
                "japanese-stable",
            ]

            if "image" in (output_modalities or []):
                model_type = "image_generation"
            elif any(p in model_name_lower for p in image_patterns):
                model_type = "image"
            elif modality and "text" in modality.lower():
                model_type = "chat"
            else:
                model_type = "chat"

            provider = extract_provider(model_id)

            model_info = ModelInfo(
                provider=provider,
                model_id=model_id,
                display_name=item.get("name", create_display_name(model_id)),
                pricing=PricingInfo(
                    input_per_million=round(input_per_million, 6),
                    output_per_million=round(output_per_million, 6),
                    cache_read_per_million=(
                        round(cache_read_per_million, 6)
                        if cache_read_per_million
                        else None
                    ),
                    cache_creation_per_million=(
                        round(cache_creation_per_million, 6)
                        if cache_creation_per_million
                        else None
                    ),
                    currency="USD",
                ),
                context_window=context_window,
                max_output_tokens=max_output,
                model_type=model_type,
                supports_vision="image" in modality.lower() if modality else False,
                supports_function_calling=True,
                supports_streaming=True,
                category=categorize_model(model_id, context_window, input_per_million),
                sources={
                    "openrouter": SourceInfo(
                        price_input=round(input_per_million, 6),
                        price_output=round(output_per_million, 6),
                        price_cache_read=(
                            round(cache_read_per_million, 6)
                            if cache_read_per_million
                            else None
                        ),
                        price_cache_creation=(
                            round(cache_creation_per_million, 6)
                            if cache_creation_per_million
                            else None
                        ),
                        last_updated=fetched_at,
                    )
                },
            )

            models[model_id] = model_info

        except (ValueError, TypeError, KeyError) as e:
            print(f"⚠ Skipping model {item.get('id', 'unknown')}: {e}")
            continue

    return models


def normalize_litellm(
    raw_data: dict[str, Any], fetched_at: str
) -> dict[str, ModelInfo]:
    """
    Transform LiteLLM format to unified schema.

    LiteLLM format (per model entry):
    {
        "max_tokens": 4096,
        "max_input_tokens": 128000,
        "input_cost_per_token": 0.00001,
        "output_cost_per_token": 0.00003,
        "cache_read_input_token_cost": 0.000001,
        "cache_creation_input_token_cost": 0.000005,
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

            # Get cache pricing (new fields)
            cache_read_cost = parse_cache_price(
                model_data.get("cache_read_input_token_cost")
            )
            cache_creation_cost = parse_cache_price(
                model_data.get("cache_creation_input_token_cost")
            )

            # Convert to per-million
            input_per_million = input_cost * 1_000_000
            output_per_million = output_cost * 1_000_000
            cache_read_per_million = (
                cache_read_cost * 1_000_000 if cache_read_cost else None
            )
            cache_creation_per_million = (
                cache_creation_cost * 1_000_000 if cache_creation_cost else None
            )

            # Skip models with no pricing data
            if input_per_million == 0 and output_per_million == 0:
                continue

            # Get context limits
            max_input = int(model_data.get("max_input_tokens", 0) or 0)
            max_output = int(
                model_data.get("max_tokens", 0)
                or model_data.get("max_output_tokens", 0)
                or 0
            )

            # LiteLLM uses litellm_provider or we extract from key
            provider = model_data.get("litellm_provider", "") or extract_provider(
                model_key
            )

            # Known model name patterns
            model_name_lower = model_key.lower()

            # Image model patterns
            image_patterns = [
                "stable-diffusion",
                "sdxl",
                "flux",
                "dall-e",
                "midjourney",
                "playground-v2",
                "ssd-1b",
                "japanese-stable",
            ]
            is_image_by_name = any(p in model_name_lower for p in image_patterns)

            # Embedding model patterns
            embedding_patterns = ["embedding", "embed"]
            is_embedding_by_name = any(p in model_name_lower for p in embedding_patterns)

            # Get model type from LiteLLM mode field
            mode = model_data.get("mode", "chat")

            # Override with name-based detection
            if is_image_by_name:
                model_type = "image"
            elif is_embedding_by_name:
                model_type = "embedding"
            elif mode in ("chat", "completion", "responses"):
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
                    input_per_million=round(input_per_million, 6),
                    output_per_million=round(output_per_million, 6),
                    cache_read_per_million=(
                        round(cache_read_per_million, 6)
                        if cache_read_per_million
                        else None
                    ),
                    cache_creation_per_million=(
                        round(cache_creation_per_million, 6)
                        if cache_creation_per_million
                        else None
                    ),
                    currency="USD",
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
                        price_input=round(input_per_million, 6),
                        price_output=round(output_per_million, 6),
                        price_cache_read=(
                            round(cache_read_per_million, 6)
                            if cache_read_per_million
                            else None
                        ),
                        price_cache_creation=(
                            round(cache_creation_per_million, 6)
                            if cache_creation_per_million
                            else None
                        ),
                        last_updated=fetched_at,
                    )
                },
            )

            models[model_key] = model_info

        except (ValueError, TypeError, KeyError) as e:
            print(f"⚠ Skipping LiteLLM model {model_key}: {e}")
            continue

    return models


def merge_sources(
    openrouter_models: dict[str, ModelInfo], litellm_models: dict[str, ModelInfo]
) -> dict[str, ModelInfo]:
    """
    Merge models from both sources.

    Strategy:
    - If model exists in both, merge sources and use OpenRouter for capabilities
    - OpenRouter is considered more accurate for capabilities (vision, function calling)
    - Both price sources are preserved for comparison
    - Cache pricing is merged: prefer non-null values from either source

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
            litellm_source = litellm_model.sources.get("litellm")
            if litellm_source:
                existing.sources["litellm"] = litellm_source

            # Merge cache pricing: prefer non-null values
            if (
                existing.pricing.cache_read_per_million is None
                and litellm_model.pricing.cache_read_per_million is not None
            ):
                existing.pricing.cache_read_per_million = (
                    litellm_model.pricing.cache_read_per_million
                )
            if (
                existing.pricing.cache_creation_per_million is None
                and litellm_model.pricing.cache_creation_per_million is not None
            ):
                existing.pricing.cache_creation_per_million = (
                    litellm_model.pricing.cache_creation_per_million
                )
        else:
            # New model from LiteLLM
            merged[model_id] = litellm_model

    return merged


def get_default_providers() -> dict[str, ProviderInfo]:
    """Return default provider information."""
    return {
        "openai": ProviderInfo(
            name="OpenAI",
            website="https://openai.com",
            pricing_page="https://openai.com/pricing",
        ),
        "anthropic": ProviderInfo(
            name="Anthropic",
            website="https://anthropic.com",
            pricing_page="https://anthropic.com/pricing",
        ),
        "google": ProviderInfo(
            name="Google",
            website="https://cloud.google.com/vertex-ai",
            pricing_page="https://cloud.google.com/vertex-ai/pricing",
        ),
        "mistral": ProviderInfo(
            name="Mistral AI",
            website="https://mistral.ai",
            pricing_page="https://mistral.ai/pricing",
        ),
        "meta": ProviderInfo(
            name="Meta",
            website="https://ai.meta.com",
            pricing_page="https://ai.meta.com/llama",
        ),
        "deepseek": ProviderInfo(
            name="DeepSeek",
            website="https://deepseek.com",
            pricing_page="https://platform.deepseek.com/pricing",
        ),
        "cohere": ProviderInfo(
            name="Cohere",
            website="https://cohere.com",
            pricing_page="https://cohere.com/pricing",
        ),
    }


def main() -> None:
    """
    Main entry point for the normalizer.

    Workflow:
    1. Load raw data from OpenRouter and LiteLLM
    2. Normalize each source to unified schema
    3. Merge sources (with cache pricing support)
    4. Generate prices.json
    """
    print("=" * 60)
    print("LLM Price Tracker - Normalizer (tokenprice fork)")
    print(f"Started at: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    # Load raw data
    print("\n📂 Loading raw data...")
    openrouter_raw = load_json(CURRENT_DIR / "openrouter.json")
    litellm_raw = load_json(CURRENT_DIR / "litellm.json")

    # Normalize each source
    print("\n🔄 Normalizing OpenRouter data...")
    openrouter_fetched = openrouter_raw.get("fetched_at", datetime.now(timezone.utc).isoformat())
    openrouter_models = normalize_openrouter(openrouter_raw, openrouter_fetched)
    print(f"✓ OpenRouter: {len(openrouter_models)} models normalized")

    # Count models with cache pricing
    or_cache_read = sum(1 for m in openrouter_models.values() if m.pricing.cache_read_per_million)
    or_cache_creation = sum(1 for m in openrouter_models.values() if m.pricing.cache_creation_per_million)
    print(f"  └─ Cache pricing: {or_cache_read} read, {or_cache_creation} creation")

    print("\n🔄 Normalizing LiteLLM data...")
    litellm_fetched = litellm_raw.get("fetched_at", datetime.now(timezone.utc).isoformat())
    litellm_models = normalize_litellm(litellm_raw, litellm_fetched)
    print(f"✓ LiteLLM: {len(litellm_models)} models normalized")

    # Count models with cache pricing
    ll_cache_read = sum(1 for m in litellm_models.values() if m.pricing.cache_read_per_million)
    ll_cache_creation = sum(1 for m in litellm_models.values() if m.pricing.cache_creation_per_million)
    print(f"  └─ Cache pricing: {ll_cache_read} read, {ll_cache_creation} creation")

    # Merge sources
    print("\n🔗 Merging sources...")
    merged_models = merge_sources(openrouter_models, litellm_models)
    print(f"✓ Merged: {len(merged_models)} unique models")

    # Count final cache pricing coverage
    final_cache_read = sum(1 for m in merged_models.values() if m.pricing.cache_read_per_million)
    final_cache_creation = sum(1 for m in merged_models.values() if m.pricing.cache_creation_per_million)
    print(f"  └─ Final cache pricing: {final_cache_read} read, {final_cache_creation} creation")

    # Build output schema
    output = PricesSchema(
        generated_at=datetime.now(timezone.utc).isoformat(),
        models={k: v for k, v in sorted(merged_models.items())},
        providers=get_default_providers(),
        metadata={
            "version": "2.0.0",
            "fork": "tokenprice",
            "original": "https://github.com/MrUnreal/LLMTracker",
            "sources": {
                "openrouter": {
                    "url": "https://openrouter.ai/api/v1/models",
                    "fetched_at": openrouter_fetched,
                    "model_count": len(openrouter_models),
                },
                "litellm": {
                    "url": "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json",
                    "fetched_at": litellm_fetched,
                    "model_count": len(litellm_models),
                },
            },
            "features": {
                "cache_pricing": True,
                "cache_read_per_million": "Cost for cache hits",
                "cache_creation_per_million": "Cost for cache writes/misses",
            },
        },
    )

    # Save output
    save_json(CURRENT_DIR / "prices.json", output.model_dump())

    print("\n" + "=" * 60)
    print("✅ Normalization completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
