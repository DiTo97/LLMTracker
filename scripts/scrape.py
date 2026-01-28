"""
LLM Price Tracker - Scraper Module (tokenprice fork)

Purpose: Fetch pricing data from OpenRouter API and LiteLLM GitHub repository.

Data Sources:
- OpenRouter API: https://openrouter.ai/api/v1/models
- LiteLLM: https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json

Output:
- data/current/openrouter.json
- data/current/litellm.json

Credits: Original implementation from https://github.com/MrUnreal/LLMTracker
"""

import json
import httpx
from pathlib import Path
from datetime import datetime, timezone
from typing import Any


# Configuration
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/models"
LITELLM_RAW_URL = "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json"

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CURRENT_DIR = DATA_DIR / "current"

# HTTP client configuration
REQUEST_TIMEOUT = 30.0  # seconds
USER_AGENT = "tokenprice/1.0 (https://github.com/DiTo97/tokenprice)"


def ensure_directories() -> None:
    """
    Create necessary directories if they don't exist.

    Creates:
    - data/current/
    - data/history/
    - data/changelog/
    """
    directories = [
        CURRENT_DIR,
        DATA_DIR / "history",
        DATA_DIR / "changelog",
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"✓ Directory ensured: {directory}")


def save_json(filepath: Path, data: Any) -> None:
    """
    Save data to a JSON file with pretty formatting.

    Args:
        filepath: Path to the output file
        data: Data to serialize to JSON

    Raises:
        IOError: If the file cannot be written
    """
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved: {filepath}")
    except IOError as e:
        raise IOError(f"Failed to save JSON to {filepath}: {e}") from e


def scrape_openrouter() -> dict[str, Any]:
    """
    Fetch model data from OpenRouter API.

    The OpenRouter API returns a list of models with pricing information.
    Each model includes:
    - id: Model identifier (e.g., "openai/gpt-4o")
    - pricing: Object with prompt, completion, input_cache_read, input_cache_write costs
    - context_length: Maximum context window size
    - top_provider: Provider information

    Returns:
        dict: Raw API response containing model data

    Raises:
        httpx.HTTPError: If the API request fails
        ValueError: If the response is not valid JSON
    """
    print(f"\n📡 Fetching OpenRouter API: {OPENROUTER_API_URL}")

    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            response = client.get(
                OPENROUTER_API_URL, headers={"User-Agent": USER_AGENT}
            )
            response.raise_for_status()

            data = response.json()

            # Validate response structure
            if not isinstance(data, dict):
                raise ValueError(f"Expected dict response, got {type(data).__name__}")

            if "data" not in data:
                raise ValueError("Response missing 'data' field")

            models = data.get("data", [])
            print(f"✓ OpenRouter: Retrieved {len(models)} models")

            # Add metadata
            result = {
                "source": "openrouter",
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "api_url": OPENROUTER_API_URL,
                "model_count": len(models),
                "data": models,
            }

            return result

    except httpx.HTTPStatusError as e:
        raise httpx.HTTPError(
            f"OpenRouter API returned status {e.response.status_code}: {e.response.text}"
        ) from e
    except httpx.RequestError as e:
        raise httpx.HTTPError(f"Failed to connect to OpenRouter API: {e}") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"OpenRouter API returned invalid JSON: {e}") from e


def scrape_litellm() -> dict[str, Any]:
    """
    Fetch model pricing data from LiteLLM GitHub repository.

    LiteLLM maintains a comprehensive JSON file with pricing for various models.
    The format is a dictionary where each key is a model name and value contains:
    - input_cost_per_token: Cost per input token (not per million)
    - output_cost_per_token: Cost per output token
    - cache_read_input_token_cost: Cost per cached input token (read/hit)
    - cache_creation_input_token_cost: Cost per cached input token (write/miss)
    - max_tokens: Maximum output tokens
    - max_input_tokens: Maximum input tokens
    - litellm_provider: Provider name

    Returns:
        dict: Raw pricing data from LiteLLM

    Raises:
        httpx.HTTPError: If the request fails
        ValueError: If the response is not valid JSON
    """
    print(f"\n📡 Fetching LiteLLM data: {LITELLM_RAW_URL}")

    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            response = client.get(LITELLM_RAW_URL, headers={"User-Agent": USER_AGENT})
            response.raise_for_status()

            data = response.json()

            # Validate response structure
            if not isinstance(data, dict):
                raise ValueError(f"Expected dict response, got {type(data).__name__}")

            print(f"✓ LiteLLM: Retrieved {len(data)} model entries")

            # Add metadata wrapper
            result = {
                "source": "litellm",
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "source_url": LITELLM_RAW_URL,
                "model_count": len(data),
                "data": data,
            }

            return result

    except httpx.HTTPStatusError as e:
        raise httpx.HTTPError(
            f"LiteLLM fetch returned status {e.response.status_code}: {e.response.text}"
        ) from e
    except httpx.RequestError as e:
        raise httpx.HTTPError(f"Failed to fetch LiteLLM data: {e}") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"LiteLLM data is not valid JSON: {e}") from e


def main() -> None:
    """
    Main entry point for the scraper.

    Workflow:
    1. Ensure output directories exist
    2. Fetch data from OpenRouter API
    3. Fetch data from LiteLLM GitHub
    4. Save both to data/current/ directory

    Raises:
        Exception: If any scraping operation fails
    """
    print("=" * 60)
    print("LLM Price Tracker - Scraper (tokenprice fork)")
    print(f"Started at: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    # Step 1: Ensure directories exist
    ensure_directories()

    # Step 2: Scrape OpenRouter
    try:
        openrouter_data = scrape_openrouter()
        save_json(CURRENT_DIR / "openrouter.json", openrouter_data)
    except Exception as e:
        print(f"❌ OpenRouter scraping failed: {e}")
        raise

    # Step 3: Scrape LiteLLM
    try:
        litellm_data = scrape_litellm()
        save_json(CURRENT_DIR / "litellm.json", litellm_data)
    except Exception as e:
        print(f"❌ LiteLLM scraping failed: {e}")
        raise

    print("\n" + "=" * 60)
    print("✅ Scraping completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
