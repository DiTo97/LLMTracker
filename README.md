# LLM Price Tracker

A fully automated LLM pricing tracker that scrapes pricing from multiple sources, detects price changes, and provides a recommendation engine.

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Support-yellow?style=flat&logo=buy-me-a-coffee)](https://buymeacoffee.com/mrunrealgit)

> ☕ **If this tool saves you money, consider [buying me a coffee](https://buymeacoffee.com/mrunrealgit)!**

## Features

- 🔄 **Automated Scraping**: Fetches pricing data every 6 hours from OpenRouter and LiteLLM
- 📊 **Price Tracking**: Historical price data stored in Git
- 🔔 **Alerts**: Discord, Slack, and email notifications for price changes
- 🔍 **Recommendation Engine**: Find the best model for your needs
- 💰 **Cost Calculator**: Estimate costs based on token usage
- 📈 **Comparison Tool**: Side-by-side model comparison

## Architecture

This project is 95% GitHub-hosted:
- **GitHub Actions**: Automated scraping and deployment
- **Git Repository**: Data storage and version control
- **GitHub Pages**: Static website hosting

## Quick Start

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/MrUnreal/LLMTracker.git
   cd llm-price-tracker
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the scraper:
   ```bash
   python scripts/scrape.py
   python scripts/normalize.py
   python scripts/detect_changes.py
   python scripts/generate_site.py
   ```

4. View the website:
   Open `website/index.html` in your browser

### GitHub Setup

1. Fork this repository
2. Enable GitHub Pages (Settings → Pages → Source: main branch, /website folder)
3. Add secrets for alerts (optional):
   - `DISCORD_WEBHOOK_URL`
   - `SLACK_WEBHOOK_URL`
   - `BUTTONDOWN_API_KEY`

## Data Sources

- **OpenRouter API**: https://openrouter.ai/api/v1/models
- **LiteLLM**: https://github.com/BerriAI/litellm/blob/main/model_prices_and_context_window.json

## API

Access the pricing data directly:

```
https://raw.githubusercontent.com/yourusername/llm-price-tracker/main/data/current/prices.json
```

## Contributing

Contributions are welcome! Please read the contributing guidelines before submitting a PR.

## License

MIT License - see LICENSE file for details.
