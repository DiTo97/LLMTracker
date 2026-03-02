# LLMTracker (fork)

This is a fork of [LLMTracker](https://github.com/MrUnreal/LLMTracker) with extended support for **cache pricing** fields.

## Why the fork?

The original LLMTracker doesn't track cache read/write token pricing, even though the source data (OpenRouter API and LiteLLM) provides this information. This fork adds:

- `cache_read_per_million`: Cost per million tokens for cache hits
- `cache_creation_per_million`: Cost per million tokens for cache writes/misses

## Features

- **Cache Pricing Support**: Track cache read and cache creation costs
- **Automated Updates**: Prices updated every 6 hours via GitHub Actions
- **Discord Alerts**: Notifications for price changes
- **Uses uv**: Modern Python package manager for fast, reproducible builds

## Setup

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
# Install dependencies
uv sync

# Run the scraper
uv run python scripts/scrape.py

# Normalize data
uv run python scripts/normalize.py

# Detect changes
uv run python scripts/detect_changes.py

# Send alerts (requires DISCORD_WEBHOOK_URL env var)
uv run python scripts/send_alerts.py
```

## Data Sources

- **OpenRouter API**: `https://openrouter.ai/api/v1/models`
  - `input_cache_read` → `cache_read_per_million`
  - `input_cache_write` → `cache_creation_per_million`

- **LiteLLM**: `https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json`
  - `cache_read_input_token_cost` → `cache_read_per_million`
  - `cache_creation_input_token_cost` → `cache_creation_per_million`

## Schema

```json
{
  "models": {
    "openai/gpt-4o": {
      "provider": "openai",
      "model_id": "openai/gpt-4o",
      "pricing": {
        "input_per_million": 2.5,
        "output_per_million": 10.0,
        "cache_read_per_million": 1.25,
        "cache_creation_per_million": null,
        "currency": "USD"
      }
    }
  }
}
```

## Environment Variables

- `WEBHOOK_URL` / `DISCORD_WEBHOOK_URL`: Discord webhook for notifications

## Credits

- Original project: [LLMTracker](https://github.com/MrUnreal/LLMTracker) by MrUnreal
- Pricing data: [OpenRouter](https://openrouter.ai), [LiteLLM](https://github.com/BerriAI/litellm)

