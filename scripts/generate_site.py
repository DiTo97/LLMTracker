"""
LLM Price Tracker - Static Site Generator

Purpose: Build static website from pricing data with professional branding.

Input:
- data/current/prices.json
- data/changelog/latest.json

Output:
- website/index.html
- website/compare.html
- website/calculator.html
- website/find.html
- website/changelog.html
- website/api.html
- website/data/prices.json (copy for client-side access)
"""

import json
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Any


# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CURRENT_DIR = DATA_DIR / "current"
CHANGELOG_DIR = DATA_DIR / "changelog"
WEBSITE_DIR = PROJECT_ROOT / "website"

# Brand colors
BRAND = {
    "primary": "#6366f1",      # Indigo-500
    "primary_dark": "#4f46e5", # Indigo-600
    "accent": "#8b5cf6",       # Violet-500
    "success": "#10b981",      # Emerald-500
    "warning": "#f59e0b",      # Amber-500
    "danger": "#ef4444",       # Red-500
}


def load_json(filepath: Path) -> dict[str, Any]:
    """Load a JSON file and return its contents."""
    if not filepath.exists():
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_file(filepath: Path, content: str) -> None:
    """Save content to a file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✓ Generated: {filepath}")


def get_common_head(title: str, description: str = "") -> str:
    """Return common HTML head content with SEO and branding."""
    desc = description or "Compare real-time pricing for 2000+ AI language models. Find the cheapest LLM for your needs."
    return f'''
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{desc}">
    <meta name="keywords" content="LLM pricing, AI model costs, GPT pricing, Claude pricing, language model comparison">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{desc}">
    <meta property="og:type" content="website">
    <meta name="twitter:card" content="summary_large_image">
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>💰</text></svg>">
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {{
            theme: {{
                extend: {{
                    colors: {{
                        brand: {{
                            50: '#eef2ff',
                            100: '#e0e7ff',
                            200: '#c7d2fe',
                            300: '#a5b4fc',
                            400: '#818cf8',
                            500: '#6366f1',
                            600: '#4f46e5',
                            700: '#4338ca',
                            800: '#3730a3',
                            900: '#312e81',
                        }}
                    }}
                }}
            }}
        }}
    </script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        * {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }}
        
        .gradient-bg {{ 
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
        }}
        .gradient-text {{
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .glass {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}
        .card-hover {{
            transition: all 0.3s ease;
        }}
        .card-hover:hover {{
            transform: translateY(-4px);
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        }}
        .price-decrease {{ color: #10b981; }}
        .price-increase {{ color: #ef4444; }}
        .animate-pulse-slow {{ animation: pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite; }}
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
        ::-webkit-scrollbar-track {{ background: #f1f5f9; }}
        ::-webkit-scrollbar-thumb {{ background: #cbd5e1; border-radius: 4px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: #94a3b8; }}
        
        /* Table styles */
        .data-table th {{ 
            position: sticky; 
            top: 0; 
            background: white; 
            z-index: 10;
            border-bottom: 2px solid #e2e8f0;
        }}
        .data-table tbody tr:hover {{ background: #f8fafc; }}
    </style>
'''


def get_nav(active_page: str = "") -> str:
    """Return navigation HTML with active state."""
    def nav_link(href: str, text: str, page_id: str) -> str:
        is_active = page_id == active_page
        base_classes = "px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200"
        if is_active:
            return f'<a href="{href}" class="{base_classes} bg-brand-100 text-brand-700">{text}</a>'
        return f'<a href="{href}" class="{base_classes} text-gray-600 hover:text-brand-600 hover:bg-brand-50">{text}</a>'
    
    return f'''
    <nav class="bg-white/95 backdrop-blur-md shadow-sm sticky top-0 z-50 border-b border-gray-100">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16">
                <div class="flex items-center">
                    <a href="index.html" class="flex items-center space-x-2 group">
                        <span class="text-2xl">💰</span>
                        <span class="text-xl font-bold bg-gradient-to-r from-brand-600 to-purple-600 bg-clip-text text-transparent">
                            LLM Prices
                        </span>
                    </a>
                </div>
                <div class="hidden md:flex items-center space-x-1">
                    {nav_link("compare.html", "📊 Compare", "compare")}
                    {nav_link("calculator.html", "🧮 Calculator", "calculator")}
                    {nav_link("find.html", "🔍 Find Model", "find")}
                    {nav_link("changelog.html", "📈 Changes", "changelog")}
                    {nav_link("api.html", "🔌 API", "api")}
                </div>
                <div class="flex items-center md:hidden">
                    <button onclick="document.getElementById('mobile-menu').classList.toggle('hidden')" 
                            class="p-2 rounded-lg text-gray-600 hover:bg-gray-100">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
                        </svg>
                    </button>
                </div>
            </div>
        </div>
        <div id="mobile-menu" class="hidden md:hidden border-t border-gray-100 bg-white px-4 py-3 space-y-1">
            <a href="compare.html" class="block px-4 py-2 rounded-lg text-gray-600 hover:bg-brand-50">📊 Compare</a>
            <a href="calculator.html" class="block px-4 py-2 rounded-lg text-gray-600 hover:bg-brand-50">🧮 Calculator</a>
            <a href="find.html" class="block px-4 py-2 rounded-lg text-gray-600 hover:bg-brand-50">🔍 Find Model</a>
            <a href="changelog.html" class="block px-4 py-2 rounded-lg text-gray-600 hover:bg-brand-50">📈 Changes</a>
            <a href="api.html" class="block px-4 py-2 rounded-lg text-gray-600 hover:bg-brand-50">🔌 API</a>
        </div>
    </nav>
'''


def get_footer() -> str:
    """Return professional footer HTML."""
    year = datetime.now().year
    return f'''
    <footer class="bg-gray-900 text-white">
        <div class="max-w-7xl mx-auto px-4 py-12">
            <div class="grid md:grid-cols-4 gap-8 mb-8">
                <div class="col-span-2">
                    <div class="flex items-center space-x-2 mb-4">
                        <span class="text-2xl">💰</span>
                        <span class="text-xl font-bold">LLM Prices</span>
                    </div>
                    <p class="text-gray-400 text-sm max-w-md">
                        Real-time pricing tracker for AI language models. Compare costs across 2000+ models 
                        from OpenAI, Anthropic, Google, Meta, and more.
                    </p>
                </div>
                <div>
                    <h4 class="font-semibold mb-4">Tools</h4>
                    <ul class="space-y-2 text-sm text-gray-400">
                        <li><a href="compare.html" class="hover:text-white transition-colors">Model Comparison</a></li>
                        <li><a href="calculator.html" class="hover:text-white transition-colors">Cost Calculator</a></li>
                        <li><a href="find.html" class="hover:text-white transition-colors">Model Finder</a></li>
                        <li><a href="api.html" class="hover:text-white transition-colors">API Access</a></li>
                    </ul>
                </div>
                <div>
                    <h4 class="font-semibold mb-4">Data Sources</h4>
                    <ul class="space-y-2 text-sm text-gray-400">
                        <li><a href="https://openrouter.ai" target="_blank" class="hover:text-white transition-colors">OpenRouter</a></li>
                        <li><a href="https://github.com/BerriAI/litellm" target="_blank" class="hover:text-white transition-colors">LiteLLM</a></li>
                        <li><a href="changelog.html" class="hover:text-white transition-colors">Price Changes</a></li>
                    </ul>
                </div>
            </div>
            <div class="border-t border-gray-800 pt-8 flex flex-col md:flex-row justify-between items-center">
                <p class="text-gray-500 text-sm">
                    Made with ❤️ by <a href="https://github.com/MrUnreal" class="text-gray-400 hover:text-white">MrUnreal</a>
                </p>
                <div class="flex items-center space-x-6 mt-4 md:mt-0">
                    <a href="https://github.com/MrUnreal/LLMTracker" class="text-gray-400 hover:text-white transition-colors flex items-center gap-2" target="_blank">
                        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path fill-rule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clip-rule="evenodd"/></svg>
                        <span class="text-sm">GitHub</span>
                    </a>
                    <a href="https://buymeacoffee.com/mrunrealgit" class="text-yellow-500 hover:text-yellow-400 transition-colors flex items-center gap-2" target="_blank">
                        <span class="text-lg">☕</span>
                        <span class="text-sm">Support</span>
                    </a>
                </div>
            </div>
        </div>
    </footer>
'''


def format_price(price: float) -> str:
    """Format price for display."""
    if price == 0:
        return "Free"
    if price < 0:
        return "N/A"
    if price < 0.01:
        return f"${price:.4f}"
    if price < 1:
        return f"${price:.3f}"
    return f"${price:.2f}"


def format_context(ctx: int) -> str:
    """Format context window for display."""
    if ctx >= 1_000_000:
        return f"{ctx / 1_000_000:.1f}M"
    if ctx >= 1_000:
        return f"{ctx // 1_000}k"
    return str(ctx)


def generate_index(prices: dict, changelog: dict) -> str:
    """Generate homepage with professional design."""
    metadata = prices.get("metadata", {})
    models = prices.get("models", {})
    total = metadata.get("total_models", len(models))
    providers = metadata.get("providers", [])
    categories = metadata.get("categories", {})
    last_update = prices.get("generated_at", "Unknown")
    
    # Format update time
    try:
        update_dt = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
        update_str = update_dt.strftime("%B %d, %Y at %H:%M UTC")
    except Exception:
        update_str = last_update
    
    # Get top 10 cheapest models (filter out negatives and zeros)
    valid_models = [
        (mid, m) for mid, m in models.items()
        if m.get("pricing", {}).get("input_per_million", -1) > 0
    ]
    sorted_models = sorted(
        valid_models,
        key=lambda x: x[1].get("pricing", {}).get("input_per_million", 999999)
    )[:10]
    
    cheapest_html = ""
    for i, (model_id, model) in enumerate(sorted_models):
        pricing = model.get("pricing", {})
        inp = format_price(pricing.get("input_per_million", 0))
        out = format_price(pricing.get("output_per_million", 0))
        name = model.get("display_name", model_id)
        provider = model.get("provider", "Unknown")
        ctx = format_context(model.get("context_window", 0))
        category = model.get("category", "standard")
        
        badge_color = {
            "flagship": "bg-purple-100 text-purple-700",
            "standard": "bg-blue-100 text-blue-700", 
            "budget": "bg-green-100 text-green-700",
            "code": "bg-amber-100 text-amber-700",
            "embedding": "bg-gray-100 text-gray-700"
        }.get(category, "bg-gray-100 text-gray-700")
        
        rank_badge = ""
        if i == 0:
            rank_badge = '<span class="ml-2 text-xs bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded-full">🏆 Best Value</span>'
        
        cheapest_html += f'''
        <tr class="border-b border-gray-100 hover:bg-gray-50 transition-colors">
            <td class="py-4 px-4">
                <div class="font-semibold text-gray-900">{name}{rank_badge}</div>
                <div class="text-sm text-gray-500">{provider}</div>
            </td>
            <td class="py-4 px-4 font-mono text-sm">{inp}</td>
            <td class="py-4 px-4 font-mono text-sm">{out}</td>
            <td class="py-4 px-4 text-sm text-gray-600">{ctx}</td>
            <td class="py-4 px-4"><span class="text-xs px-2 py-1 rounded-full {badge_color}">{category}</span></td>
        </tr>'''
    
    # Category stats
    cat_html = ""
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        cat_html += f'<span class="px-3 py-1 bg-gray-100 rounded-full text-sm text-gray-700">{cat}: {count}</span>'
    
    # Recent changes
    changes = changelog.get("changes", [])[:5]
    changes_html = ""
    for change in changes:
        model_id = change.get("model_id", "")
        ctype = change.get("change_type", "")
        pct = change.get("percent_change", 0)
        if ctype == "price_decrease":
            icon = "📉"
            color = "text-green-600"
            pct_str = f"({pct:.1f}%)" if pct else ""
        elif ctype == "price_increase":
            icon = "📈"
            color = "text-red-600"
            pct_str = f"(+{abs(pct):.1f}%)" if pct else ""
        else:
            icon = "🆕"
            color = "text-blue-600"
            pct_str = ""
        changes_html += f'''
        <div class="flex items-center justify-between py-3 border-b border-gray-100 last:border-0">
            <div class="flex items-center space-x-3">
                <span class="text-xl">{icon}</span>
                <span class="font-medium text-gray-900">{model_id.split("/")[-1]}</span>
            </div>
            <span class="{color} font-semibold">{pct_str}</span>
        </div>'''
    
    if not changes_html:
        changes_html = '''
        <div class="text-center py-8 text-gray-500">
            <span class="text-4xl mb-2 block">✨</span>
            <p>No recent price changes</p>
            <p class="text-sm">Prices are stable</p>
        </div>'''
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <title>LLM Price Tracker - Compare AI Model Pricing in Real-Time</title>
    {get_common_head("LLM Price Tracker", "Compare real-time pricing for 2000+ AI language models from OpenAI, Anthropic, Google, Meta, and more.")}
</head>
<body class="bg-gradient-to-br from-gray-50 to-gray-100 min-h-screen">
    {get_nav("home")}
    
    <!-- Hero Section -->
    <header class="gradient-bg text-white py-20 relative overflow-hidden">
        <div class="absolute inset-0 bg-black/10"></div>
        <div class="absolute -top-24 -right-24 w-96 h-96 bg-white/10 rounded-full blur-3xl"></div>
        <div class="absolute -bottom-24 -left-24 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl"></div>
        <div class="max-w-7xl mx-auto px-4 text-center relative">
            <div class="inline-flex items-center bg-white/20 backdrop-blur-sm px-4 py-2 rounded-full text-sm mb-6">
                <span class="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></span>
                Updated every 6 hours
            </div>
            <h1 class="text-5xl md:text-6xl font-extrabold mb-6 tracking-tight">
                LLM Price Tracker
            </h1>
            <p class="text-xl md:text-2xl mb-8 text-white/90 max-w-2xl mx-auto">
                Compare pricing for <span class="font-bold">{total:,}</span> AI models from {len(providers)}+ providers.
                Find the best value for your needs.
            </p>
            <div class="flex flex-wrap justify-center gap-4">
                <a href="find.html" class="bg-white text-brand-600 px-8 py-4 rounded-xl font-semibold hover:bg-gray-100 transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-1">
                    🔍 Find a Model
                </a>
                <a href="compare.html" class="bg-white/20 backdrop-blur-sm text-white px-8 py-4 rounded-xl font-semibold hover:bg-white/30 transition-all border border-white/30">
                    📊 Compare All
                </a>
            </div>
            <p class="text-sm text-white/70 mt-6">Last updated: {update_str}</p>
        </div>
    </header>
    
    <!-- Support Banner -->
    <div class="max-w-7xl mx-auto px-4 -mt-4 mb-4 relative z-20">
        <a href="https://buymeacoffee.com/mrunrealgit" target="_blank" 
           class="block bg-gradient-to-r from-yellow-50 to-orange-50 border border-yellow-200 rounded-xl p-4 hover:shadow-md transition-all group">
            <div class="flex items-center justify-center gap-3 text-center">
                <span class="text-2xl">☕</span>
                <span class="text-gray-700">If this tool saves you money on AI costs, consider <span class="font-semibold text-yellow-700 group-hover:text-yellow-800">buying me a coffee</span>!</span>
                <span class="text-yellow-600 group-hover:translate-x-1 transition-transform">→</span>
            </div>
        </a>
    </div>
    
    <main class="max-w-7xl mx-auto px-4 py-12 -mt-8 relative z-10">
        <!-- Stats Cards -->
        <div class="grid md:grid-cols-4 gap-6 mb-12">
            <div class="bg-white rounded-2xl shadow-lg p-6 text-center card-hover">
                <div class="w-12 h-12 bg-brand-100 rounded-xl flex items-center justify-center mx-auto mb-4">
                    <span class="text-2xl">🤖</span>
                </div>
                <div class="text-4xl font-bold text-gray-900">{total:,}</div>
                <div class="text-gray-600 text-sm">Models Tracked</div>
            </div>
            <div class="bg-white rounded-2xl shadow-lg p-6 text-center card-hover">
                <div class="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center mx-auto mb-4">
                    <span class="text-2xl">🏢</span>
                </div>
                <div class="text-4xl font-bold text-gray-900">{len(providers)}</div>
                <div class="text-gray-600 text-sm">Providers</div>
            </div>
            <div class="bg-white rounded-2xl shadow-lg p-6 text-center card-hover">
                <div class="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center mx-auto mb-4">
                    <span class="text-2xl">📊</span>
                </div>
                <div class="text-4xl font-bold text-gray-900">{len(categories)}</div>
                <div class="text-gray-600 text-sm">Categories</div>
            </div>
            <div class="bg-white rounded-2xl shadow-lg p-6 text-center card-hover">
                <div class="w-12 h-12 bg-amber-100 rounded-xl flex items-center justify-center mx-auto mb-4">
                    <span class="text-2xl">⏱️</span>
                </div>
                <div class="text-4xl font-bold text-gray-900">6h</div>
                <div class="text-gray-600 text-sm">Update Frequency</div>
            </div>
        </div>
        
        <!-- Categories Pills -->
        <div class="bg-white rounded-2xl shadow-lg p-6 mb-8">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">Categories</h3>
            <div class="flex flex-wrap gap-2">
                {cat_html}
            </div>
        </div>
        
        <!-- Main Content Grid -->
        <div class="grid lg:grid-cols-3 gap-8">
            <!-- Cheapest Models Table -->
            <div class="lg:col-span-2 bg-white rounded-2xl shadow-lg overflow-hidden">
                <div class="p-6 border-b border-gray-100">
                    <div class="flex items-center justify-between">
                        <h2 class="text-xl font-bold text-gray-900">💰 Top 10 Cheapest Models</h2>
                        <a href="compare.html" class="text-brand-600 hover:text-brand-700 text-sm font-medium">
                            View all →
                        </a>
                    </div>
                    <p class="text-gray-500 text-sm mt-1">Sorted by input price per million tokens</p>
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full data-table">
                        <thead>
                            <tr class="text-left text-gray-500 text-sm uppercase tracking-wider">
                                <th class="py-3 px-4 font-semibold">Model</th>
                                <th class="py-3 px-4 font-semibold">Input/M</th>
                                <th class="py-3 px-4 font-semibold">Output/M</th>
                                <th class="py-3 px-4 font-semibold">Context</th>
                                <th class="py-3 px-4 font-semibold">Category</th>
                            </tr>
                        </thead>
                        <tbody>{cheapest_html}</tbody>
                    </table>
                </div>
            </div>
            
            <!-- Recent Changes -->
            <div class="bg-white rounded-2xl shadow-lg">
                <div class="p-6 border-b border-gray-100">
                    <div class="flex items-center justify-between">
                        <h2 class="text-xl font-bold text-gray-900">📈 Recent Changes</h2>
                        <a href="changelog.html" class="text-brand-600 hover:text-brand-700 text-sm font-medium">
                            View all →
                        </a>
                    </div>
                </div>
                <div class="p-6">
                    {changes_html}
                </div>
            </div>
        </div>
        
        <!-- CTA Section -->
        <div class="mt-12 bg-gradient-to-r from-brand-600 to-purple-600 rounded-2xl p-8 text-white text-center relative overflow-hidden">
            <div class="absolute -top-12 -right-12 w-48 h-48 bg-white/10 rounded-full blur-2xl"></div>
            <div class="relative">
                <h2 class="text-2xl md:text-3xl font-bold mb-4">🔔 Never Miss a Price Drop</h2>
                <p class="text-white/90 mb-6 max-w-lg mx-auto">
                    Get instant notifications when LLM prices change. Be the first to save on AI costs.
                </p>
                <div class="flex flex-col sm:flex-row gap-4 justify-center">
                    <a href="https://buttondown.email/llm-price-tracker" target="_blank" 
                       class="bg-white text-brand-600 px-8 py-3 rounded-xl font-semibold hover:bg-gray-100 transition-all shadow-lg">
                        📧 Subscribe to Alerts
                    </a>
                    <a href="https://discord.gg/yourinvite" target="_blank"
                       class="bg-white/20 backdrop-blur-sm text-white px-8 py-3 rounded-xl font-semibold hover:bg-white/30 transition-all border border-white/30">
                        💬 Join Discord
                    </a>
                </div>
            </div>
        </div>
        
        <!-- Quick Links -->
        <div class="mt-12 grid md:grid-cols-3 gap-6">
            <a href="calculator.html" class="bg-white rounded-2xl shadow-lg p-6 card-hover group">
                <div class="text-3xl mb-4">🧮</div>
                <h3 class="text-lg font-bold text-gray-900 group-hover:text-brand-600 transition-colors">Cost Calculator</h3>
                <p class="text-gray-500 text-sm mt-2">Estimate your monthly costs based on token usage</p>
            </a>
            <a href="find.html" class="bg-white rounded-2xl shadow-lg p-6 card-hover group">
                <div class="text-3xl mb-4">🔍</div>
                <h3 class="text-lg font-bold text-gray-900 group-hover:text-brand-600 transition-colors">Find Perfect Model</h3>
                <p class="text-gray-500 text-sm mt-2">Get recommendations based on your requirements</p>
            </a>
            <a href="api.html" class="bg-white rounded-2xl shadow-lg p-6 card-hover group">
                <div class="text-3xl mb-4">🔌</div>
                <h3 class="text-lg font-bold text-gray-900 group-hover:text-brand-600 transition-colors">API Access</h3>
                <p class="text-gray-500 text-sm mt-2">Integrate pricing data into your own applications</p>
            </a>
        </div>
    </main>
    
    {get_footer()}
</body>
</html>'''


def generate_compare(prices: dict) -> str:
    """Generate model comparison page."""
    models = prices.get("models", {})
    providers = sorted(set(m.get("provider", "Unknown") for m in models.values()))
    categories = sorted(set(m.get("category", "standard") for m in models.values()))
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <title>Compare LLM Prices - Side by Side Model Comparison</title>
    {get_common_head("Compare LLM Prices", "Compare pricing for all AI language models side by side. Filter by provider, category, and features.")}
</head>
<body class="bg-gradient-to-br from-gray-50 to-gray-100 min-h-screen">
    {get_nav("compare")}
    
    <main class="max-w-7xl mx-auto px-4 py-8">
        <!-- Header -->
        <div class="mb-8">
            <h1 class="text-3xl font-bold text-gray-900 mb-2">📊 Compare All Models</h1>
            <p class="text-gray-600">Filter and compare pricing across {len(models):,} AI models</p>
        </div>
        
        <!-- Filters -->
        <div class="bg-white rounded-2xl shadow-lg p-6 mb-8">
            <div class="grid md:grid-cols-4 gap-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Search</label>
                    <input type="text" id="search" placeholder="Search models..." 
                           class="w-full px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none transition-all">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Provider</label>
                    <select id="provider" class="w-full px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none appearance-none bg-white cursor-pointer">
                        <option value="">All Providers</option>
                        {"".join(f'<option value="{p}">{p}</option>' for p in providers)}
                    </select>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Category</label>
                    <select id="category" class="w-full px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none appearance-none bg-white cursor-pointer">
                        <option value="">All Categories</option>
                        {"".join(f'<option value="{c}">{c.title()}</option>' for c in categories)}
                    </select>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Sort By</label>
                    <select id="sort" class="w-full px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none appearance-none bg-white cursor-pointer">
                        <option value="input_asc">Price: Low to High</option>
                        <option value="input_desc">Price: High to Low</option>
                        <option value="name">Name A-Z</option>
                        <option value="context_desc">Context: Largest First</option>
                    </select>
                </div>
            </div>
            <div class="mt-4 flex items-center justify-between">
                <div class="text-sm text-gray-500">
                    Showing <span id="count" class="font-semibold text-brand-600">0</span> models
                </div>
                <button onclick="resetFilters()" class="text-sm text-brand-600 hover:text-brand-700 font-medium">
                    Reset Filters
                </button>
            </div>
        </div>
        
        <!-- Table -->
        <div class="bg-white rounded-2xl shadow-lg overflow-hidden">
            <div class="overflow-x-auto">
                <table class="w-full data-table" id="models-table">
                    <thead>
                        <tr class="text-left text-gray-500 text-xs uppercase tracking-wider bg-gray-50">
                            <th class="py-4 px-4 font-semibold">Model</th>
                            <th class="py-4 px-4 font-semibold">Provider</th>
                            <th class="py-4 px-4 font-semibold">Input $/M</th>
                            <th class="py-4 px-4 font-semibold">Output $/M</th>
                            <th class="py-4 px-4 font-semibold">Context</th>
                            <th class="py-4 px-4 font-semibold">Category</th>
                            <th class="py-4 px-4 font-semibold">Features</th>
                        </tr>
                    </thead>
                    <tbody id="models-body">
                        <tr><td colspan="7" class="py-12 text-center text-gray-500">Loading models...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Support CTA -->
        <div class="mt-8 text-center">
            <a href="https://buymeacoffee.com/mrunrealgit" target="_blank" 
               class="inline-flex items-center gap-2 text-gray-500 hover:text-yellow-600 transition-colors group">
                <span class="text-lg group-hover:animate-bounce">☕</span>
                <span class="text-sm">Found a cheaper model? <span class="font-medium text-yellow-600">Buy me a coffee</span></span>
            </a>
        </div>
    </main>
    
    {get_footer()}
    
    <script>
        let allModels = [];
        
        async function loadData() {{
            const response = await fetch('data/prices.json');
            const data = await response.json();
            allModels = Object.entries(data.models || {{}}).map(([id, m]) => ({{
                id, ...m,
                input: m.pricing?.input_per_million || 0,
                output: m.pricing?.output_per_million || 0
            }}));
            applyFilters();
        }}
        
        function formatPrice(p) {{
            if (p === 0) return '<span class="text-green-600 font-medium">Free</span>';
            if (p < 0) return '<span class="text-gray-400">N/A</span>';
            if (p < 0.01) return '$' + p.toFixed(4);
            if (p < 1) return '$' + p.toFixed(3);
            return '$' + p.toFixed(2);
        }}
        
        function formatContext(ctx) {{
            if (!ctx) return '-';
            if (ctx >= 1000000) return (ctx/1000000).toFixed(1) + 'M';
            if (ctx >= 1000) return Math.floor(ctx/1000) + 'k';
            return ctx.toString();
        }}
        
        function getCategoryBadge(cat) {{
            const colors = {{
                flagship: 'bg-purple-100 text-purple-700',
                standard: 'bg-blue-100 text-blue-700',
                budget: 'bg-green-100 text-green-700',
                code: 'bg-amber-100 text-amber-700',
                embedding: 'bg-gray-100 text-gray-700'
            }};
            return `<span class="text-xs px-2 py-1 rounded-full ${{colors[cat] || colors.standard}}">${{cat}}</span>`;
        }}
        
        function applyFilters() {{
            const search = document.getElementById('search').value.toLowerCase();
            const provider = document.getElementById('provider').value;
            const category = document.getElementById('category').value;
            const sort = document.getElementById('sort').value;
            
            let filtered = allModels.filter(m => {{
                if (search && !m.display_name?.toLowerCase().includes(search) && !m.id.toLowerCase().includes(search)) return false;
                if (provider && m.provider !== provider) return false;
                if (category && m.category !== category) return false;
                return true;
            }});
            
            // Sort
            filtered.sort((a, b) => {{
                switch(sort) {{
                    case 'input_asc': return (a.input || 999999) - (b.input || 999999);
                    case 'input_desc': return (b.input || 0) - (a.input || 0);
                    case 'name': return (a.display_name || '').localeCompare(b.display_name || '');
                    case 'context_desc': return (b.context_window || 0) - (a.context_window || 0);
                    default: return 0;
                }}
            }});
            
            document.getElementById('count').textContent = filtered.length.toLocaleString();
            
            const tbody = document.getElementById('models-body');
            if (filtered.length === 0) {{
                tbody.innerHTML = '<tr><td colspan="7" class="py-12 text-center text-gray-500">No models match your filters</td></tr>';
                return;
            }}
            
            tbody.innerHTML = filtered.slice(0, 500).map(m => `
                <tr class="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                    <td class="py-3 px-4">
                        <div class="font-medium text-gray-900">${{m.display_name || m.id}}</div>
                        <div class="text-xs text-gray-400 font-mono">${{m.id}}</div>
                    </td>
                    <td class="py-3 px-4 text-sm text-gray-600">${{m.provider || '-'}}</td>
                    <td class="py-3 px-4 font-mono text-sm">${{formatPrice(m.input)}}</td>
                    <td class="py-3 px-4 font-mono text-sm">${{formatPrice(m.output)}}</td>
                    <td class="py-3 px-4 text-sm text-gray-600">${{formatContext(m.context_window)}}</td>
                    <td class="py-3 px-4">${{getCategoryBadge(m.category || 'standard')}}</td>
                    <td class="py-3 px-4">
                        <div class="flex gap-1">
                            ${{m.supports_vision ? '<span class="text-xs bg-purple-100 text-purple-600 px-1.5 py-0.5 rounded">Vision</span>' : ''}}
                            ${{m.supports_function_calling ? '<span class="text-xs bg-blue-100 text-blue-600 px-1.5 py-0.5 rounded">Functions</span>' : ''}}
                        </div>
                    </td>
                </tr>
            `).join('');
        }}
        
        function resetFilters() {{
            document.getElementById('search').value = '';
            document.getElementById('provider').value = '';
            document.getElementById('category').value = '';
            document.getElementById('sort').value = 'input_asc';
            applyFilters();
        }}
        
        document.getElementById('search').addEventListener('input', applyFilters);
        document.getElementById('provider').addEventListener('change', applyFilters);
        document.getElementById('category').addEventListener('change', applyFilters);
        document.getElementById('sort').addEventListener('change', applyFilters);
        
        loadData();
    </script>
</body>
</html>'''


def generate_calculator(prices: dict) -> str:
    """Generate cost calculator page."""
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <title>LLM Cost Calculator - Estimate Your AI Spending</title>
    {get_common_head("LLM Cost Calculator", "Calculate and compare LLM API costs based on your token usage. Find the cheapest model for your needs.")}
</head>
<body class="bg-gradient-to-br from-gray-50 to-gray-100 min-h-screen">
    {get_nav("calculator")}
    
    <main class="max-w-5xl mx-auto px-4 py-8">
        <div class="mb-8">
            <h1 class="text-3xl font-bold text-gray-900 mb-2">🧮 Cost Calculator</h1>
            <p class="text-gray-600">Estimate your LLM API costs based on token usage</p>
        </div>
        
        <div class="grid lg:grid-cols-2 gap-8">
            <!-- Input Form -->
            <div class="bg-white rounded-2xl shadow-lg p-6">
                <h2 class="text-lg font-semibold text-gray-900 mb-6">Configure Usage</h2>
                
                <div class="space-y-6">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Search Model</label>
                        <div class="relative">
                            <input type="text" id="model-search" placeholder="Type to search (e.g. gpt-4, claude, llama...)" 
                                   autocomplete="off"
                                   class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none">
                            <div id="search-results" class="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-xl shadow-lg max-h-80 overflow-y-auto hidden">
                            </div>
                        </div>
                        <div id="selected-model" class="mt-3 p-3 bg-brand-50 border border-brand-200 rounded-xl hidden">
                            <div class="flex justify-between items-start">
                                <div>
                                    <div class="font-medium text-gray-900" id="selected-name">-</div>
                                    <div class="text-sm text-gray-500" id="selected-provider">-</div>
                                </div>
                                <div class="text-right">
                                    <div class="text-sm font-medium text-brand-600" id="selected-prices">-</div>
                                    <button onclick="clearSelection()" class="text-xs text-gray-400 hover:text-red-500">✕ Clear</button>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Input Tokens</label>
                            <input type="number" id="input-tokens" value="100000" min="0" step="1000"
                                   class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-brand-500 outline-none">
                            <p class="text-xs text-gray-500 mt-1">Per request</p>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Output Tokens</label>
                            <input type="number" id="output-tokens" value="50000" min="0" step="1000"
                                   class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-brand-500 outline-none">
                            <p class="text-xs text-gray-500 mt-1">Per request</p>
                        </div>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Requests per Day</label>
                        <input type="number" id="requests" value="100" min="1" step="10"
                               class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-brand-500 outline-none">
                    </div>
                </div>
            </div>
            
            <!-- Results -->
            <div class="bg-white rounded-2xl shadow-lg p-6">
                <h2 class="text-lg font-semibold text-gray-900 mb-6">Estimated Costs</h2>
                
                <div class="space-y-4">
                    <div class="bg-gradient-to-r from-brand-500 to-purple-500 rounded-xl p-6 text-white">
                        <div class="text-sm opacity-90 mb-1">Monthly Cost</div>
                        <div class="text-4xl font-bold" id="monthly-cost">$0.00</div>
                    </div>
                    
                    <div class="grid grid-cols-2 gap-4">
                        <div class="bg-gray-50 rounded-xl p-4">
                            <div class="text-sm text-gray-600 mb-1">Per Request</div>
                            <div class="text-xl font-semibold text-gray-900" id="per-request">$0.00</div>
                        </div>
                        <div class="bg-gray-50 rounded-xl p-4">
                            <div class="text-sm text-gray-600 mb-1">Daily Cost</div>
                            <div class="text-xl font-semibold text-gray-900" id="daily-cost">$0.00</div>
                        </div>
                    </div>
                    
                    <div class="border-t border-gray-100 pt-4">
                        <div class="flex justify-between text-sm mb-2">
                            <span class="text-gray-600">Input cost</span>
                            <span class="font-medium" id="input-cost">$0.00</span>
                        </div>
                        <div class="flex justify-between text-sm">
                            <span class="text-gray-600">Output cost</span>
                            <span class="font-medium" id="output-cost">$0.00</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Alternatives -->
        <div class="mt-8 bg-white rounded-2xl shadow-lg p-6">
            <h2 class="text-lg font-semibold text-gray-900 mb-4">💡 Cheaper Alternatives</h2>
            <div id="alternatives" class="grid md:grid-cols-3 gap-4">
                <p class="text-gray-500 col-span-3 text-center py-4">Select a model to see alternatives</p>
            </div>
        </div>
        
        <!-- Support CTA -->
        <div class="mt-8 text-center">
            <a href="https://buymeacoffee.com/mrunrealgit" target="_blank" 
               class="inline-flex items-center gap-2 text-gray-500 hover:text-yellow-600 transition-colors group">
                <span class="text-lg group-hover:animate-bounce">☕</span>
                <span class="text-sm">Did this help? <span class="font-medium text-yellow-600">Buy me a coffee</span></span>
            </a>
        </div>
    </main>
    
    {get_footer()}
    
    <script>
        let modelsData = {{}};
        let selectedModelId = null;
        let searchTimeout = null;
        
        async function loadData() {{
            const response = await fetch('data/prices.json');
            const data = await response.json();
            modelsData = data.models || {{}};
            
            // Auto-select first popular model if available
            const popular = ['openai/gpt-4o-mini', 'anthropic/claude-3.5-sonnet', 'openai/gpt-4o'];
            for (const id of popular) {{
                if (modelsData[id]) {{
                    selectModel(id);
                    break;
                }}
            }}
        }}
        
        function searchModels(query) {{
            if (!query || query.length < 2) {{
                document.getElementById('search-results').classList.add('hidden');
                return;
            }}
            
            const q = query.toLowerCase();
            const results = Object.entries(modelsData)
                .filter(([id, m]) => {{
                    const name = (m.display_name || '').toLowerCase();
                    const provider = (m.provider || '').toLowerCase();
                    return name.includes(q) || id.toLowerCase().includes(q) || provider.includes(q);
                }})
                .sort((a, b) => {{
                    // Prioritize exact matches and popular providers
                    const aName = (a[1].display_name || a[0]).toLowerCase();
                    const bName = (b[1].display_name || b[0]).toLowerCase();
                    if (aName.startsWith(q) && !bName.startsWith(q)) return -1;
                    if (!aName.startsWith(q) && bName.startsWith(q)) return 1;
                    return (a[1].pricing?.input_per_million || 0) - (b[1].pricing?.input_per_million || 0);
                }})
                .slice(0, 20);
            
            const container = document.getElementById('search-results');
            if (results.length === 0) {{
                container.innerHTML = '<div class="p-4 text-gray-500 text-sm">No models found</div>';
            }} else {{
                container.innerHTML = results.map(([id, m]) => {{
                    const inp = m.pricing?.input_per_million;
                    const out = m.pricing?.output_per_million;
                    const priceStr = inp === 0 ? '<span class="text-green-600">Free</span>' : '$' + (inp?.toFixed(2) || '?') + '/$' + (out?.toFixed(2) || '?');
                    return `
                        <div class="px-4 py-3 hover:bg-gray-50 cursor-pointer border-b border-gray-100 last:border-0" onclick="selectModel('${{id}}')">
                            <div class="flex justify-between items-start">
                                <div>
                                    <div class="font-medium text-gray-900">${{m.display_name || id}}</div>
                                    <div class="text-xs text-gray-500">${{m.provider || 'Unknown'}} • ${{m.category || 'standard'}}</div>
                                </div>
                                <div class="text-sm text-brand-600 font-medium">${{priceStr}}</div>
                            </div>
                        </div>
                    `;
                }}).join('');
            }}
            container.classList.remove('hidden');
        }}
        
        function selectModel(id) {{
            selectedModelId = id;
            const model = modelsData[id];
            if (!model) return;
            
            document.getElementById('model-search').value = '';
            document.getElementById('search-results').classList.add('hidden');
            
            const inp = model.pricing?.input_per_million?.toFixed(2) || '0.00';
            const out = model.pricing?.output_per_million?.toFixed(2) || '0.00';
            
            document.getElementById('selected-name').textContent = model.display_name || id;
            document.getElementById('selected-provider').textContent = (model.provider || 'Unknown') + ' • ' + (model.category || 'standard');
            document.getElementById('selected-prices').textContent = '$' + inp + ' input / $' + out + ' output per M tokens';
            document.getElementById('selected-model').classList.remove('hidden');
            
            calculate();
        }}
        
        function clearSelection() {{
            selectedModelId = null;
            document.getElementById('selected-model').classList.add('hidden');
            document.getElementById('monthly-cost').textContent = '$0.00';
            document.getElementById('per-request').textContent = '$0.0000';
            document.getElementById('daily-cost').textContent = '$0.00';
            document.getElementById('input-cost').textContent = '$0.00';
            document.getElementById('output-cost').textContent = '$0.00';
            document.getElementById('alternatives').innerHTML = '<p class="text-gray-500 col-span-3 text-center py-4">Select a model to see alternatives</p>';
        }}
        
        function calculate() {{
            if (!selectedModelId) return;
            const model = modelsData[selectedModelId];
            if (!model) return;
            
            const inputTokens = parseInt(document.getElementById('input-tokens').value) || 0;
            const outputTokens = parseInt(document.getElementById('output-tokens').value) || 0;
            const requests = parseInt(document.getElementById('requests').value) || 0;
            
            const inputPrice = model.pricing?.input_per_million || 0;
            const outputPrice = model.pricing?.output_per_million || 0;
            
            const inputCostPerReq = (inputTokens / 1000000) * inputPrice;
            const outputCostPerReq = (outputTokens / 1000000) * outputPrice;
            const costPerRequest = inputCostPerReq + outputCostPerReq;
            const dailyCost = costPerRequest * requests;
            const monthlyCost = dailyCost * 30;
            
            document.getElementById('per-request').textContent = '$' + costPerRequest.toFixed(4);
            document.getElementById('daily-cost').textContent = '$' + dailyCost.toFixed(2);
            document.getElementById('monthly-cost').textContent = '$' + monthlyCost.toFixed(2);
            document.getElementById('input-cost').textContent = '$' + (inputCostPerReq * requests * 30).toFixed(2);
            document.getElementById('output-cost').textContent = '$' + (outputCostPerReq * requests * 30).toFixed(2);
            
            // Find alternatives
            const alternatives = Object.entries(modelsData)
                .filter(([id, m]) => {{
                    if (id === selectedModelId) return false;
                    const inp = m.pricing?.input_per_million || 0;
                    return inp > 0 && inp < inputPrice * 0.8;
                }})
                .sort((a, b) => (a[1].pricing?.input_per_million || 0) - (b[1].pricing?.input_per_million || 0))
                .slice(0, 6);
            
            const altContainer = document.getElementById('alternatives');
            if (inputPrice === 0) {{
                altContainer.innerHTML = '<p class="text-gray-500 col-span-3 text-center py-4">You selected a free model - great choice!</p>';
            }} else if (alternatives.length === 0) {{
                altContainer.innerHTML = '<p class="text-gray-500 col-span-3 text-center py-4">This is already one of the cheapest options!</p>';
            }} else {{
                altContainer.innerHTML = alternatives.map(([id, m]) => {{
                    const altInput = m.pricing?.input_per_million || 0;
                    const altOutput = m.pricing?.output_per_million || 0;
                    const altCost = ((inputTokens / 1000000) * altInput + (outputTokens / 1000000) * altOutput) * requests * 30;
                    const savings = monthlyCost > 0 ? ((monthlyCost - altCost) / monthlyCost * 100).toFixed(0) : 0;
                    return `
                        <div class="border border-gray-200 rounded-xl p-4 hover:border-brand-300 transition-colors cursor-pointer" onclick="selectModel('${{id}}')">
                            <div class="font-medium text-gray-900 mb-1">${{m.display_name || id}}</div>
                            <div class="text-sm text-gray-500 mb-2">${{m.provider}}</div>
                            <div class="flex items-baseline gap-2">
                                <span class="text-lg font-semibold text-green-600">$${{altCost.toFixed(2)}}/mo</span>
                                <span class="text-xs text-green-600">Save ${{savings}}%</span>
                            </div>
                        </div>
                    `;
                }}).join('');
            }}
        }}
        
        // Event listeners
        const searchInput = document.getElementById('model-search');
        searchInput.addEventListener('input', (e) => {{
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => searchModels(e.target.value), 150);
        }});
        
        searchInput.addEventListener('focus', (e) => {{
            if (e.target.value.length >= 2) searchModels(e.target.value);
        }});
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {{
            if (!e.target.closest('#model-search') && !e.target.closest('#search-results')) {{
                document.getElementById('search-results').classList.add('hidden');
            }}
        }});
        
        document.getElementById('input-tokens').addEventListener('input', calculate);
        document.getElementById('output-tokens').addEventListener('input', calculate);
        document.getElementById('requests').addEventListener('input', calculate);
        
        loadData();
    </script>
</body>
</html>'''


def generate_find(prices: dict) -> str:
    """Generate model finder/recommendation page."""
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <title>Find the Perfect LLM - Model Recommendation Engine</title>
    {get_common_head("Find the Perfect LLM", "Get personalized AI model recommendations based on your requirements. Filter by price, context window, and features.")}
</head>
<body class="bg-gradient-to-br from-gray-50 to-gray-100 min-h-screen">
    {get_nav("find")}
    
    <main class="max-w-6xl mx-auto px-4 py-8">
        <div class="mb-8">
            <h1 class="text-3xl font-bold text-gray-900 mb-2">🔍 Find the Perfect Model</h1>
            <p class="text-gray-600">Tell us what you need and we'll recommend the best models</p>
        </div>
        
        <div class="grid lg:grid-cols-3 gap-8">
            <!-- Filters -->
            <div class="lg:col-span-1">
                <div class="bg-white rounded-2xl shadow-lg p-6 sticky top-24">
                    <h2 class="text-lg font-semibold text-gray-900 mb-6">I need a model that...</h2>
                    
                    <div class="space-y-6">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">
                                Max Input Price <span class="text-gray-400">($/M tokens)</span>
                            </label>
                            <input type="range" id="max-price" min="0" max="50" value="10" step="0.5"
                                   class="w-full accent-brand-500">
                            <div class="flex justify-between text-xs text-gray-500 mt-1">
                                <span>$0</span>
                                <span id="price-display" class="font-medium text-brand-600">$10</span>
                                <span>$50+</span>
                            </div>
                        </div>
                        
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Min Context Window</label>
                            <select id="min-context" class="w-full px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-brand-500 outline-none">
                                <option value="0">Any</option>
                                <option value="8000">8k+</option>
                                <option value="32000">32k+</option>
                                <option value="64000">64k+</option>
                                <option value="128000" selected>128k+</option>
                                <option value="200000">200k+</option>
                            </select>
                        </div>
                        
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-3">Features</label>
                            <div class="space-y-2">
                                <label class="flex items-center gap-3 cursor-pointer">
                                    <input type="checkbox" id="vision" class="w-4 h-4 rounded text-brand-500 focus:ring-brand-500">
                                    <span class="text-sm text-gray-700">Vision (images)</span>
                                </label>
                                <label class="flex items-center gap-3 cursor-pointer">
                                    <input type="checkbox" id="functions" class="w-4 h-4 rounded text-brand-500 focus:ring-brand-500">
                                    <span class="text-sm text-gray-700">Function Calling</span>
                                </label>
                                <label class="flex items-center gap-3 cursor-pointer">
                                    <input type="checkbox" id="streaming" checked class="w-4 h-4 rounded text-brand-500 focus:ring-brand-500">
                                    <span class="text-sm text-gray-700">Streaming</span>
                                </label>
                            </div>
                        </div>
                        
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-3">Category</label>
                            <div class="flex flex-wrap gap-2">
                                <button onclick="setCategory('')" class="cat-btn active px-3 py-1.5 text-sm rounded-lg border transition-all" data-cat="">All</button>
                                <button onclick="setCategory('flagship')" class="cat-btn px-3 py-1.5 text-sm rounded-lg border transition-all" data-cat="flagship">Flagship</button>
                                <button onclick="setCategory('standard')" class="cat-btn px-3 py-1.5 text-sm rounded-lg border transition-all" data-cat="standard">Standard</button>
                                <button onclick="setCategory('budget')" class="cat-btn px-3 py-1.5 text-sm rounded-lg border transition-all" data-cat="budget">Budget</button>
                                <button onclick="setCategory('code')" class="cat-btn px-3 py-1.5 text-sm rounded-lg border transition-all" data-cat="code">Code</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Results -->
            <div class="lg:col-span-2">
                <div class="flex items-center justify-between mb-4">
                    <h2 class="text-lg font-semibold text-gray-900">Recommendations</h2>
                    <span id="result-count" class="text-sm text-gray-500">0 models found</span>
                </div>
                <div id="results" class="space-y-4">
                    <p class="text-gray-500 text-center py-12">Loading...</p>
                </div>
                
                <!-- Support CTA -->
                <div class="mt-8 text-center">
                    <a href="https://buymeacoffee.com/mrunrealgit" target="_blank" 
                       class="inline-flex items-center gap-2 text-gray-500 hover:text-yellow-600 transition-colors group">
                        <span class="text-lg group-hover:animate-bounce">☕</span>
                        <span class="text-sm">Found the perfect model? <span class="font-medium text-yellow-600">Buy me a coffee</span></span>
                    </a>
                </div>
            </div>
        </div>
    </main>
    
    {get_footer()}
    
    <style>
        .cat-btn {{ background: white; border-color: #e5e7eb; color: #6b7280; }}
        .cat-btn:hover {{ border-color: #a5b4fc; }}
        .cat-btn.active {{ background: #eef2ff; border-color: #6366f1; color: #4f46e5; }}
    </style>
    
    <script>
        let allModels = [];
        let selectedCategory = '';
        
        async function loadData() {{
            const response = await fetch('data/prices.json');
            const data = await response.json();
            allModels = Object.entries(data.models || {{}}).map(([id, m]) => ({{
                id, ...m,
                input: m.pricing?.input_per_million || 0,
                output: m.pricing?.output_per_million || 0
            }}));
            applyFilters();
        }}
        
        function setCategory(cat) {{
            selectedCategory = cat;
            document.querySelectorAll('.cat-btn').forEach(btn => {{
                btn.classList.toggle('active', btn.dataset.cat === cat);
            }});
            applyFilters();
        }}
        
        function applyFilters() {{
            const maxPrice = parseFloat(document.getElementById('max-price').value);
            const minContext = parseInt(document.getElementById('min-context').value);
            const needsVision = document.getElementById('vision').checked;
            const needsFunctions = document.getElementById('functions').checked;
            const needsStreaming = document.getElementById('streaming').checked;
            
            document.getElementById('price-display').textContent = maxPrice >= 50 ? '$50+' : '$' + maxPrice;
            
            let filtered = allModels.filter(m => {{
                if (m.input <= 0 || m.input > maxPrice) return false;
                if ((m.context_window || 0) < minContext) return false;
                if (needsVision && !m.supports_vision) return false;
                if (needsFunctions && !m.supports_function_calling) return false;
                if (needsStreaming && !m.supports_streaming) return false;
                if (selectedCategory && m.category !== selectedCategory) return false;
                return true;
            }});
            
            filtered.sort((a, b) => a.input - b.input);
            
            document.getElementById('result-count').textContent = filtered.length + ' models found';
            
            const container = document.getElementById('results');
            if (filtered.length === 0) {{
                container.innerHTML = '<div class="text-center py-12 text-gray-500"><span class="text-4xl block mb-2">🔍</span>No models match your criteria. Try adjusting filters.</div>';
                return;
            }}
            
            container.innerHTML = filtered.slice(0, 20).map((m, i) => `
                <div class="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
                    <div class="flex items-start justify-between mb-4">
                        <div>
                            <h3 class="text-lg font-semibold text-gray-900">${{m.display_name || m.id}}</h3>
                            <p class="text-sm text-gray-500">${{m.provider}} • ${{m.id}}</p>
                        </div>
                        ${{i === 0 ? '<span class="bg-yellow-100 text-yellow-700 text-xs font-medium px-2 py-1 rounded-full">⭐ Best Match</span>' : ''}}
                    </div>
                    <div class="grid grid-cols-3 gap-4 mb-4">
                        <div>
                            <div class="text-xs text-gray-500 mb-1">Input</div>
                            <div class="font-semibold text-gray-900">$${{m.input.toFixed(2)}}/M</div>
                        </div>
                        <div>
                            <div class="text-xs text-gray-500 mb-1">Output</div>
                            <div class="font-semibold text-gray-900">$${{m.output.toFixed(2)}}/M</div>
                        </div>
                        <div>
                            <div class="text-xs text-gray-500 mb-1">Context</div>
                            <div class="font-semibold text-gray-900">${{m.context_window >= 1000000 ? (m.context_window/1000000).toFixed(1) + 'M' : Math.floor((m.context_window||0)/1000) + 'k'}}</div>
                        </div>
                    </div>
                    <div class="flex flex-wrap gap-2 mb-4">
                        ${{m.supports_vision ? '<span class="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded-full">Vision</span>' : ''}}
                        ${{m.supports_function_calling ? '<span class="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full">Functions</span>' : ''}}
                        ${{m.supports_streaming ? '<span class="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">Streaming</span>' : ''}}
                        <span class="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded-full">${{m.category || 'standard'}}</span>
                    </div>
                    <div class="flex gap-2">
                        <a href="https://openrouter.ai" target="_blank" class="flex-1 text-center bg-brand-500 text-white py-2 rounded-lg text-sm font-medium hover:bg-brand-600 transition-colors">
                            Try on OpenRouter
                        </a>
                        <a href="calculator.html" class="px-4 py-2 border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors">
                            Calculate
                        </a>
                    </div>
                </div>
            `).join('');
        }}
        
        document.getElementById('max-price').addEventListener('input', applyFilters);
        document.getElementById('min-context').addEventListener('change', applyFilters);
        document.getElementById('vision').addEventListener('change', applyFilters);
        document.getElementById('functions').addEventListener('change', applyFilters);
        document.getElementById('streaming').addEventListener('change', applyFilters);
        
        loadData();
    </script>
</body>
</html>'''


def generate_changelog(changelog: dict) -> str:
    """Generate changelog/history page with all historical changes."""
    # Load all changelog files
    all_changelogs = _load_all_changelogs()
    
    # Calculate overall summary
    total_decreases = sum(c.get("summary", {}).get("price_decreases", 0) for c in all_changelogs)
    total_increases = sum(c.get("summary", {}).get("price_increases", 0) for c in all_changelogs)
    total_new = sum(c.get("summary", {}).get("new_models", 0) for c in all_changelogs)
    total_removed = sum(c.get("summary", {}).get("removed_models", 0) for c in all_changelogs)
    
    # Generate timeline HTML
    timeline_html = _generate_timeline(all_changelogs)
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <title>LLM Price Changes - Track AI Model Pricing History</title>
    {get_common_head("LLM Price Changes", "Track all LLM price changes in real-time. See price drops, increases, and new models as they happen.")}
    <style>
        .timeline-item:before {{
            content: '';
            position: absolute;
            left: 24px;
            top: 48px;
            bottom: 0;
            width: 2px;
            background: linear-gradient(to bottom, #e5e7eb, transparent);
        }}
        .timeline-item:last-child:before {{
            display: none;
        }}
    </style>
</head>
<body class="bg-gradient-to-br from-gray-50 to-gray-100 min-h-screen">
    {get_nav("changelog")}
    
    <main class="max-w-4xl mx-auto px-4 py-8">
        <div class="text-center mb-10">
            <h1 class="text-4xl font-bold text-gray-900 mb-3">📈 Price Changelog</h1>
            <p class="text-lg text-gray-600 max-w-2xl mx-auto">Track every LLM pricing change as it happens. Never miss a price drop again.</p>
        </div>
        
        <!-- All-Time Summary Stats -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
            <div class="bg-white rounded-xl shadow-lg border border-green-100 p-5 text-center transform hover:scale-105 transition-transform">
                <div class="text-3xl font-bold text-green-600">{total_decreases}</div>
                <div class="text-sm text-gray-600 font-medium">Price Drops</div>
                <div class="text-xs text-green-500 mt-1">💰 Savings!</div>
            </div>
            <div class="bg-white rounded-xl shadow-lg border border-red-100 p-5 text-center transform hover:scale-105 transition-transform">
                <div class="text-3xl font-bold text-red-600">{total_increases}</div>
                <div class="text-sm text-gray-600 font-medium">Price Increases</div>
                <div class="text-xs text-red-500 mt-1">📈 Watch out</div>
            </div>
            <div class="bg-white rounded-xl shadow-lg border border-blue-100 p-5 text-center transform hover:scale-105 transition-transform">
                <div class="text-3xl font-bold text-blue-600">{total_new}</div>
                <div class="text-sm text-gray-600 font-medium">New Models</div>
                <div class="text-xs text-blue-500 mt-1">🆕 Fresh arrivals</div>
            </div>
            <div class="bg-white rounded-xl shadow-lg border border-gray-200 p-5 text-center transform hover:scale-105 transition-transform">
                <div class="text-3xl font-bold text-gray-600">{total_removed}</div>
                <div class="text-sm text-gray-600 font-medium">Discontinued</div>
                <div class="text-xs text-gray-500 mt-1">👋 Goodbye</div>
            </div>
        </div>
        
        <!-- Subscribe CTA (prominent) -->
        <div class="mb-10 bg-gradient-to-r from-brand-500 via-purple-500 to-pink-500 rounded-2xl p-6 md:p-8 text-white shadow-xl">
            <div class="flex flex-col md:flex-row items-center justify-between gap-4">
                <div>
                    <h2 class="text-xl md:text-2xl font-bold mb-1">🔔 Never Miss a Price Drop</h2>
                    <p class="text-white/90 text-sm md:text-base">Get instant email alerts when your favorite models get cheaper</p>
                </div>
                <a href="https://buttondown.email/llm-price-tracker" target="_blank" 
                   class="whitespace-nowrap bg-white text-brand-600 px-6 py-3 rounded-xl font-semibold hover:bg-gray-100 transition-all hover:shadow-lg">
                    Subscribe Free →
                </a>
            </div>
        </div>
        
        <!-- Timeline -->
        <div class="space-y-0">
            {timeline_html if timeline_html else _render_no_changes()}
        </div>
    </main>
    
    {get_footer()}
</body>
</html>'''


def _load_all_changelogs() -> list[dict]:
    """Load all changelog files sorted by date (newest first)."""
    changelog_dir = Path(__file__).parent.parent / "data" / "changelog"
    changelogs = []
    
    if not changelog_dir.exists():
        return []
    
    for file in sorted(changelog_dir.glob("*.json"), reverse=True):
        if file.name == "latest.json":
            continue  # Skip latest.json, we'll use dated files
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Extract date from filename (2025-12-29.json)
                date_str = file.stem
                data["_date"] = date_str
                changelogs.append(data)
        except Exception:
            continue
    
    return changelogs


def _generate_timeline(changelogs: list[dict]) -> str:
    """Generate HTML for the changelog timeline."""
    if not changelogs:
        return ""
    
    html_parts = []
    
    for cl in changelogs:
        date_str = cl.get("_date", "Unknown")
        changes = cl.get("changes", [])
        summary = cl.get("summary", {})
        
        # Format date nicely
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%B %d, %Y")
            day_name = date_obj.strftime("%A")
        except ValueError:
            formatted_date = date_str
            day_name = ""
        
        # Group changes by type for better display
        decreases = [c for c in changes if c.get("change_type") == "price_decrease"]
        increases = [c for c in changes if c.get("change_type") == "price_increase"]
        new_models = [c for c in changes if c.get("change_type") == "new_model"]
        removed = [c for c in changes if c.get("change_type") == "removed_model"]
        
        # Build changes HTML
        changes_html = ""
        
        if decreases:
            changes_html += _render_change_group("📉 Price Drops", decreases, "green")
        if increases:
            changes_html += _render_change_group("📈 Price Increases", increases, "red")
        if new_models:
            changes_html += _render_change_group("🆕 New Models", new_models, "blue")
        if removed:
            changes_html += _render_change_group("❌ Discontinued", removed, "gray")
        
        html_parts.append(f'''
        <div class="timeline-item relative pl-16 pb-10">
            <!-- Date Marker -->
            <div class="absolute left-0 top-0 w-12 h-12 bg-gradient-to-br from-brand-500 to-purple-500 rounded-xl flex items-center justify-center shadow-lg">
                <span class="text-white font-bold text-sm">{date_obj.day if 'date_obj' in dir() else '?'}</span>
            </div>
            
            <!-- Content -->
            <div class="bg-white rounded-2xl shadow-lg overflow-hidden border border-gray-100">
                <!-- Header -->
                <div class="px-6 py-4 bg-gradient-to-r from-gray-50 to-white border-b border-gray-100">
                    <div class="flex items-center justify-between">
                        <div>
                            <h3 class="text-lg font-bold text-gray-900">{formatted_date}</h3>
                            <p class="text-sm text-gray-500">{day_name}</p>
                        </div>
                        <div class="flex items-center gap-3 text-sm">
                            <span class="flex items-center gap-1 text-green-600"><span class="w-2 h-2 bg-green-500 rounded-full"></span>{summary.get("price_decreases", 0)} drops</span>
                            <span class="flex items-center gap-1 text-blue-600"><span class="w-2 h-2 bg-blue-500 rounded-full"></span>{summary.get("new_models", 0)} new</span>
                        </div>
                    </div>
                </div>
                
                <!-- Changes -->
                <div class="p-6 space-y-6">
                    {changes_html}
                </div>
            </div>
        </div>
        ''')
    
    return "".join(html_parts)


def _render_change_group(title: str, changes: list[dict], color: str) -> str:
    """Render a group of changes (e.g., all price drops)."""
    items_html = ""
    
    for change in changes:
        model_name = change.get("display_name", change.get("model_id", "Unknown"))
        provider = change.get("provider", "")
        ctype = change.get("change_type", "")
        
        if ctype == "price_decrease":
            field = change.get("field", "").replace("_per_million", "").replace("_", " ").title()
            old_val = change.get("old_value", 0)
            new_val = change.get("new_value", 0)
            pct = abs(change.get("percent_change", 0))
            items_html += f'''
            <div class="flex items-center justify-between py-2 px-3 bg-green-50 rounded-lg">
                <div>
                    <span class="font-medium text-gray-900">{model_name}</span>
                    <span class="text-gray-400 text-sm ml-2">{provider}</span>
                </div>
                <div class="text-right">
                    <div class="text-sm"><span class="text-gray-400 line-through">${old_val:.2f}</span> → <span class="text-green-600 font-bold">${new_val:.2f}</span></div>
                    <div class="text-xs text-green-600 font-medium">-{pct:.0f}% {field}</div>
                </div>
            </div>
            '''
        elif ctype == "price_increase":
            field = change.get("field", "").replace("_per_million", "").replace("_", " ").title()
            old_val = change.get("old_value", 0)
            new_val = change.get("new_value", 0)
            pct = abs(change.get("percent_change", 0))
            items_html += f'''
            <div class="flex items-center justify-between py-2 px-3 bg-red-50 rounded-lg">
                <div>
                    <span class="font-medium text-gray-900">{model_name}</span>
                    <span class="text-gray-400 text-sm ml-2">{provider}</span>
                </div>
                <div class="text-right">
                    <div class="text-sm"><span class="text-gray-400 line-through">${old_val:.2f}</span> → <span class="text-red-600 font-bold">${new_val:.2f}</span></div>
                    <div class="text-xs text-red-600 font-medium">+{pct:.0f}% {field}</div>
                </div>
            </div>
            '''
        elif ctype == "new_model":
            pricing = change.get("pricing") or {}
            input_price = pricing.get("input_per_million", 0)
            output_price = pricing.get("output_per_million", 0)
            items_html += f'''
            <div class="flex items-center justify-between py-2 px-3 bg-blue-50 rounded-lg">
                <div>
                    <span class="font-medium text-gray-900">{model_name}</span>
                    <span class="text-gray-400 text-sm ml-2">{provider}</span>
                </div>
                <div class="text-right">
                    <div class="text-sm text-blue-600 font-medium">${input_price:.2f} / ${output_price:.2f}</div>
                    <div class="text-xs text-gray-500">input / output per M</div>
                </div>
            </div>
            '''
        else:  # removed
            items_html += f'''
            <div class="flex items-center justify-between py-2 px-3 bg-gray-100 rounded-lg">
                <div>
                    <span class="font-medium text-gray-500 line-through">{model_name}</span>
                    <span class="text-gray-400 text-sm ml-2">{provider}</span>
                </div>
                <div class="text-gray-500 text-sm">Discontinued</div>
            </div>
            '''
    
    return f'''
    <div>
        <h4 class="text-sm font-semibold text-{color}-700 mb-3">{title}</h4>
        <div class="space-y-2">
            {items_html}
        </div>
    </div>
    '''


def _render_change(change: dict) -> str:
    """Render a single change item."""
    ctype = change.get("change_type", "")
    model_id = change.get("model_id", "")
    field = change.get("field", "")
    old_val = change.get("old_value", 0)
    new_val = change.get("new_value", 0)
    pct = change.get("percent_change", 0)
    
    if ctype == "price_decrease":
        icon = "📉"
        color = "text-green-600"
        bg = "bg-green-50"
        msg = f"{field}: ${old_val:.4f} → ${new_val:.4f} ({pct:.1f}%)"
    elif ctype == "price_increase":
        icon = "📈"
        color = "text-red-600"
        bg = "bg-red-50"
        msg = f"{field}: ${old_val:.4f} → ${new_val:.4f} (+{abs(pct):.1f}%)"
    elif ctype == "new_model":
        icon = "🆕"
        color = "text-blue-600"
        bg = "bg-blue-50"
        msg = "New model added"
    else:
        icon = "❌"
        color = "text-gray-600"
        bg = "bg-gray-50"
        msg = "Model removed"
    
    return f'''
    <div class="p-4 hover:bg-gray-50 transition-colors">
        <div class="flex items-center gap-4">
            <div class="text-2xl">{icon}</div>
            <div class="flex-1">
                <div class="font-medium text-gray-900">{model_id}</div>
                <div class="text-sm {color}">{msg}</div>
            </div>
            <span class="text-xs px-2 py-1 rounded-full {bg} {color}">{ctype.replace('_', ' ').title()}</span>
        </div>
    </div>'''


def _render_no_changes() -> str:
    """Render empty state for no changes."""
    return '''
    <div class="p-12 text-center">
        <span class="text-5xl block mb-4">✨</span>
        <h3 class="text-xl font-semibold text-gray-900 mb-2">No Recent Changes</h3>
        <p class="text-gray-500">Prices have been stable. Check back later!</p>
    </div>'''


def generate_api(prices: dict) -> str:
    """Generate API documentation page."""
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <title>LLM Price API - Free Pricing Data Access</title>
    {get_common_head("LLM Price API", "Free API access to LLM pricing data. No authentication required. Updated every 6 hours.")}
</head>
<body class="bg-gradient-to-br from-gray-50 to-gray-100 min-h-screen">
    {get_nav("api")}
    
    <main class="max-w-4xl mx-auto px-4 py-8">
        <div class="mb-8">
            <h1 class="text-3xl font-bold text-gray-900 mb-2">🔌 API Documentation</h1>
            <p class="text-gray-600">Access LLM pricing data programmatically</p>
        </div>
        
        <!-- Overview -->
        <div class="bg-white rounded-2xl shadow-lg p-6 mb-8">
            <h2 class="text-lg font-semibold text-gray-900 mb-4">Overview</h2>
            <p class="text-gray-600 mb-4">
                All pricing data is available as static JSON files. No authentication required. 
                Data is updated automatically every 6 hours.
            </p>
            <div class="bg-amber-50 border border-amber-200 rounded-xl p-4">
                <div class="flex items-start gap-3">
                    <span class="text-amber-500">⚠️</span>
                    <div>
                        <p class="font-medium text-amber-800">Fair Use Policy</p>
                        <p class="text-sm text-amber-700">Please cache responses on your end. The data only updates every 6 hours.</p>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Endpoints -->
        <div class="space-y-6">
            <div class="bg-white rounded-2xl shadow-lg p-6">
                <h3 class="text-lg font-semibold text-gray-900 mb-2">Current Prices</h3>
                <code class="block bg-gray-900 text-green-400 p-4 rounded-xl text-sm mb-4 overflow-x-auto">
                    GET https://raw.githubusercontent.com/yourusername/llm-price-tracker/main/data/current/prices.json
                </code>
                <p class="text-gray-600 text-sm">Returns normalized pricing for all models.</p>
            </div>
            
            <div class="bg-white rounded-2xl shadow-lg p-6">
                <h3 class="text-lg font-semibold text-gray-900 mb-2">Latest Changes</h3>
                <code class="block bg-gray-900 text-green-400 p-4 rounded-xl text-sm mb-4 overflow-x-auto">
                    GET https://raw.githubusercontent.com/yourusername/llm-price-tracker/main/data/changelog/latest.json
                </code>
                <p class="text-gray-600 text-sm">Returns the most recent price changes.</p>
            </div>
            
            <div class="bg-white rounded-2xl shadow-lg p-6">
                <h3 class="text-lg font-semibold text-gray-900 mb-2">Historical Data</h3>
                <code class="block bg-gray-900 text-green-400 p-4 rounded-xl text-sm mb-4 overflow-x-auto">
                    GET https://raw.githubusercontent.com/yourusername/llm-price-tracker/main/data/history/YYYY/MM/DD.json
                </code>
                <p class="text-gray-600 text-sm">Daily snapshots stored by date.</p>
            </div>
        </div>
        
        <!-- Code Examples -->
        <div class="bg-white rounded-2xl shadow-lg p-6 mt-8">
            <h2 class="text-lg font-semibold text-gray-900 mb-4">Code Examples</h2>
            
            <div class="space-y-4">
                <div>
                    <h4 class="font-medium text-gray-900 mb-2">JavaScript</h4>
                    <pre class="bg-gray-900 text-gray-100 p-4 rounded-xl text-sm overflow-x-auto"><code>const res = await fetch('data/prices.json');
const data = await res.json();

// Find cheapest model
const cheapest = Object.values(data.models)
  .filter(m => m.pricing.input_per_million > 0)
  .sort((a, b) => a.pricing.input_per_million - b.pricing.input_per_million)[0];

console.log(cheapest.display_name, cheapest.pricing);</code></pre>
                </div>
                
                <div>
                    <h4 class="font-medium text-gray-900 mb-2">Python</h4>
                    <pre class="bg-gray-900 text-gray-100 p-4 rounded-xl text-sm overflow-x-auto"><code>import requests

data = requests.get("https://.../prices.json").json()

# Get all OpenAI models
openai = [m for m in data["models"].values() if m["provider"] == "openai"]
for m in openai:
    print(f"{{m['display_name']}}: ${{m['pricing']['input_per_million']}}/M")</code></pre>
                </div>
                
                <div>
                    <h4 class="font-medium text-gray-900 mb-2">cURL</h4>
                    <pre class="bg-gray-900 text-gray-100 p-4 rounded-xl text-sm overflow-x-auto"><code>curl -s https://.../prices.json | jq '.metadata'</code></pre>
                </div>
            </div>
        </div>
        
        <!-- Data Sources -->
        <div class="bg-white rounded-2xl shadow-lg p-6 mt-8">
            <h2 class="text-lg font-semibold text-gray-900 mb-4">Data Sources</h2>
            <ul class="space-y-2">
                <li class="flex items-center gap-2">
                    <span class="w-2 h-2 bg-brand-500 rounded-full"></span>
                    <a href="https://openrouter.ai/api/v1/models" target="_blank" class="text-brand-600 hover:underline">OpenRouter API</a>
                </li>
                <li class="flex items-center gap-2">
                    <span class="w-2 h-2 bg-purple-500 rounded-full"></span>
                    <a href="https://github.com/BerriAI/litellm" target="_blank" class="text-brand-600 hover:underline">LiteLLM Model Prices</a>
                </li>
            </ul>
        </div>
    </main>
    
    {get_footer()}
</body>
</html>'''


def main() -> None:
    """Generate all website pages."""
    print("=" * 60)
    print("LLM Price Tracker - Site Generator")
    print("=" * 60)
    
    # Load data
    prices = load_json(CURRENT_DIR / "prices.json")
    changelog = load_json(CHANGELOG_DIR / "latest.json")
    
    print(f"✓ Loaded {len(prices.get('models', {}))} models")
    
    # Ensure website directory exists
    WEBSITE_DIR.mkdir(parents=True, exist_ok=True)
    (WEBSITE_DIR / "data").mkdir(exist_ok=True)
    
    # Copy prices.json for client-side access
    if (CURRENT_DIR / "prices.json").exists():
        shutil.copy(CURRENT_DIR / "prices.json", WEBSITE_DIR / "data" / "prices.json")
        print("✓ Copied prices.json to website/data/")
    
    # Copy changelog for client-side access
    if (CHANGELOG_DIR / "latest.json").exists():
        shutil.copy(CHANGELOG_DIR / "latest.json", WEBSITE_DIR / "data" / "changelog.json")
        print("✓ Copied changelog.json to website/data/")
    
    # Generate all pages
    print("\n🔨 Generating pages...")
    
    save_file(WEBSITE_DIR / "index.html", generate_index(prices, changelog))
    print("  ✓ index.html")
    
    save_file(WEBSITE_DIR / "compare.html", generate_compare(prices))
    print("  ✓ compare.html")
    
    save_file(WEBSITE_DIR / "calculator.html", generate_calculator(prices))
    print("  ✓ calculator.html")
    
    save_file(WEBSITE_DIR / "find.html", generate_find(prices))
    print("  ✓ find.html")
    
    save_file(WEBSITE_DIR / "changelog.html", generate_changelog(changelog))
    print("  ✓ changelog.html")
    
    save_file(WEBSITE_DIR / "api.html", generate_api(prices))
    print("  ✓ api.html")
    
    print("\n✅ Site generation completed! 6 pages generated.")


if __name__ == "__main__":
    main()
