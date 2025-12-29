# 💰 LLM Price Tracker

**Compare pricing for 2,100+ AI models from OpenRouter and LiteLLM. Updated every 6 hours.**

🌐 **[Live Site](https://mrunreal.github.io/LLMTracker/)** · 📊 [Compare Models](https://mrunreal.github.io/LLMTracker/compare.html) · 🧮 [Cost Calculator](https://mrunreal.github.io/LLMTracker/calculator.html)

---

## Features

| Feature | Description |
|---------|-------------|
| 📊 **Model Comparison** | Side-by-side comparison of 2,100+ models with sorting and filtering |
| 🧮 **Cost Calculator** | Estimate monthly costs based on your token usage |
| 🔍 **Model Finder** | Find models by category, price range, or context window |
| 📈 **Price Changes** | Track historical price changes over time |
| 🔌 **Free API** | Access raw JSON data for your own applications |

## Data Sources

Pricing data is aggregated from:

- **[OpenRouter](https://openrouter.ai/)** — 350+ models with real-time pricing
- **[LiteLLM](https://github.com/BerriAI/litellm)** — 2,200+ model configurations

Data is automatically updated every 6 hours via GitHub Actions.

## Raw Data

Access the pricing data directly as JSON (no authentication required):

```
https://raw.githubusercontent.com/MrUnreal/LLMTracker/main/data/current/prices.json
```

See the [data documentation](https://mrunreal.github.io/LLMTracker/api.html) for schema details.

## How It Works

1. **GitHub Actions** scrapes pricing APIs every 6 hours
2. **Data is normalized** into a unified schema and committed to Git
3. **Static website** is regenerated and deployed to GitHub Pages
4. **Price changes** are detected and logged in the changelog

No databases, no servers — just Git as the source of truth.

## License

MIT License

---

<sub>If this tool saves you money, consider [buying me a coffee](https://buymeacoffee.com/mrunrealgit) ☕</sub>
