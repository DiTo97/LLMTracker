"""
LLM Price Tracker - Alert Sender Module

Purpose: Send notifications to Discord, Slack, and Email when price changes are detected.

Input:
- data/changelog/latest.json

Environment Variables:
- DISCORD_WEBHOOK_URL: Discord webhook for notifications
- SLACK_WEBHOOK_URL: Slack webhook for notifications  
- BUTTONDOWN_API_KEY: Buttondown API key for email alerts
"""

import json
import os
import sys
import argparse
import httpx
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Optional


# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CHANGELOG_DIR = DATA_DIR / "changelog"

# Configuration
WEBSITE_URL = "https://mrunreal.github.io/LLMTracker"
REQUEST_TIMEOUT = 30.0


def load_json(filepath: Path) -> dict[str, Any]:
    """Load a JSON file and return its contents."""
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def format_price(price: float) -> str:
    """Format price for display."""
    if price < 0.01:
        return f"${price:.4f}"
    elif price < 1:
        return f"${price:.3f}"
    else:
        return f"${price:.2f}"


def format_percent(percent: Optional[float]) -> str:
    """Format percent change for display."""
    if percent is None:
        return ""
    sign = "+" if percent > 0 else ""
    return f"({sign}{percent:.1f}%)"


def format_change_line(change: dict[str, Any], include_links: bool = False) -> str:
    """
    Format a single change for text display.
    
    Args:
        change: The change dictionary
        include_links: If True, include Discord markdown links to calculator
        
    Returns:
        Formatted change line string
    """
    model_id = change.get("model_id", "unknown")
    change_type = change.get("change_type", "")
    field = change.get("field", "")
    old_value = change.get("old_value")
    new_value = change.get("new_value")
    percent = change.get("percent_change")
    
    # Get short model name
    model_name = model_id.split("/")[-1] if "/" in model_id else model_id
    
    # Create linked model name for Discord
    if include_links:
        from urllib.parse import quote
        calc_url = f"{WEBSITE_URL}/calculator.html?model={quote(model_id)}"
        model_display = f"[{model_name}]({calc_url})"
    else:
        model_display = model_name
    
    if change_type == "new_model":
        if isinstance(new_value, dict):
            input_price = new_value.get("input_per_million", 0)
            output_price = new_value.get("output_per_million", 0)
            return f"• {model_display}: {format_price(input_price)}/{format_price(output_price)} per M tokens"
        return f"• {model_display}"
    
    elif change_type == "removed_model":
        return f"• {model_name}"  # No link for removed models
    
    elif change_type in ("price_increase", "price_decrease"):
        field_name = "input" if "input" in field else "output"
        arrow = "→"
        return f"• {model_display} ({field_name}): {format_price(old_value)} {arrow} {format_price(new_value)} {format_percent(percent)}"
    
    else:
        return f"• {model_display}: {field} changed"


def format_discord_message(changelog: dict[str, Any]) -> dict[str, Any]:
    """
    Create Discord embed format.
    
    Uses Discord embeds with colors:
    - Green (0x00ff00) for price decreases
    - Red (0xff0000) for price increases
    - Blue (0x0099ff) for new models
    
    Args:
        changelog: Changelog data
        
    Returns:
        Discord webhook payload
    """
    summary = changelog.get("summary", {})
    changes = changelog.get("changes", [])
    
    # Determine dominant change type for color
    if summary.get("price_decreases", 0) > summary.get("price_increases", 0):
        color = 0x00ff00  # Green
        emoji = "📉"
    elif summary.get("price_increases", 0) > 0:
        color = 0xff0000  # Red
        emoji = "📈"
    else:
        color = 0x0099ff  # Blue
        emoji = "🔔"
    
    # Build description
    lines = [f"{emoji} **LLM Price Alert**\n"]
    
    # Group changes by type
    price_decreases = [c for c in changes if c.get("change_type") == "price_decrease"]
    price_increases = [c for c in changes if c.get("change_type") == "price_increase"]
    new_models = [c for c in changes if c.get("change_type") == "new_model"]
    removed_models = [c for c in changes if c.get("change_type") == "removed_model"]
    
    if price_decreases:
        lines.append("**📉 Price Decreases:**")
        for change in price_decreases[:10]:  # Limit to 10
            lines.append(format_change_line(change, include_links=True))
        if len(price_decreases) > 10:
            lines.append(f"  ...and {len(price_decreases) - 10} more")
        lines.append("")
    
    if price_increases:
        lines.append("**📈 Price Increases:**")
        for change in price_increases[:10]:
            lines.append(format_change_line(change, include_links=True))
        if len(price_increases) > 10:
            lines.append(f"  ...and {len(price_increases) - 10} more")
        lines.append("")
    
    if new_models:
        lines.append("**🆕 New Models:**")
        for change in new_models[:10]:
            lines.append(format_change_line(change, include_links=True))
        if len(new_models) > 10:
            lines.append(f"  ...and {len(new_models) - 10} more")
        lines.append("")
    
    if removed_models:
        lines.append("**🗑️ Removed Models:**")
        for change in removed_models[:5]:
            lines.append(format_change_line(change))  # No links for removed
        if len(removed_models) > 5:
            lines.append(f"  ...and {len(removed_models) - 5} more")
    
    # Add quick links section
    lines.append("")
    lines.append("**🔗 Quick Links:**")
    lines.append(f"[📊 Compare Models]({WEBSITE_URL}/compare.html) • [🧮 Calculator]({WEBSITE_URL}/calculator.html) • [📁 Raw Data]({WEBSITE_URL}/api.html)")
    
    description = "\n".join(lines)
    
    # Truncate if too long (Discord limit is 4096)
    if len(description) > 4000:
        description = description[:3997] + "..."
    
    embed = {
        "title": "LLM Price Tracker Update",
        "description": description,
        "url": f"{WEBSITE_URL}/changelog.html",
        "color": color,
        "footer": {
            "text": "Click title for full changelog • LLM Price Tracker"
        },
        "timestamp": changelog.get("generated_at", datetime.now(timezone.utc).isoformat())
    }
    
    return {
        "embeds": [embed]
    }


def format_slack_message(changelog: dict[str, Any]) -> dict[str, Any]:
    """
    Create Slack Block Kit format.
    
    Args:
        changelog: Changelog data
        
    Returns:
        Slack webhook payload
    """
    summary = changelog.get("summary", {})
    changes = changelog.get("changes", [])
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🔔 LLM Price Alert",
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Summary:* {summary.get('price_decreases', 0)} decreases, {summary.get('price_increases', 0)} increases, {summary.get('new_models', 0)} new models"
            }
        },
        {"type": "divider"}
    ]
    
    # Group changes by type
    price_decreases = [c for c in changes if c.get("change_type") == "price_decrease"]
    price_increases = [c for c in changes if c.get("change_type") == "price_increase"]
    new_models = [c for c in changes if c.get("change_type") == "new_model"]
    
    if price_decreases:
        text = "*📉 Price Decreases:*\n"
        for change in price_decreases[:8]:
            text += format_change_line(change) + "\n"
        if len(price_decreases) > 8:
            text += f"_...and {len(price_decreases) - 8} more_"
        
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": text}
        })
    
    if price_increases:
        text = "*📈 Price Increases:*\n"
        for change in price_increases[:8]:
            text += format_change_line(change) + "\n"
        if len(price_increases) > 8:
            text += f"_...and {len(price_increases) - 8} more_"
        
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": text}
        })
    
    if new_models:
        text = "*🆕 New Models:*\n"
        for change in new_models[:8]:
            text += format_change_line(change) + "\n"
        if len(new_models) > 8:
            text += f"_...and {len(new_models) - 8} more_"
        
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": text}
        })
    
    # Add footer with link
    blocks.append({"type": "divider"})
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"<{WEBSITE_URL}/changelog|View full changelog>"
            }
        ]
    })
    
    return {"blocks": blocks}


def format_email(changelog: dict[str, Any]) -> tuple[str, str]:
    """
    Create HTML email body for Buttondown.
    
    Args:
        changelog: Changelog data
        
    Returns:
        Tuple of (subject, html_body)
    """
    summary = changelog.get("summary", {})
    changes = changelog.get("changes", [])
    
    total_changes = (
        summary.get("price_decreases", 0) +
        summary.get("price_increases", 0) +
        summary.get("new_models", 0)
    )
    
    subject = f"🔔 LLM Price Alert: {total_changes} changes detected"
    
    # Build HTML body
    html_parts = [
        "<h2>🔔 LLM Price Alert</h2>",
        f"<p><strong>Summary:</strong> {summary.get('price_decreases', 0)} price decreases, ",
        f"{summary.get('price_increases', 0)} price increases, {summary.get('new_models', 0)} new models</p>",
        "<hr>"
    ]
    
    # Group changes
    price_decreases = [c for c in changes if c.get("change_type") == "price_decrease"]
    price_increases = [c for c in changes if c.get("change_type") == "price_increase"]
    new_models = [c for c in changes if c.get("change_type") == "new_model"]
    
    if price_decreases:
        html_parts.append("<h3>📉 Price Decreases</h3><ul>")
        for change in price_decreases[:15]:
            html_parts.append(f"<li>{format_change_line(change)[2:]}</li>")  # Remove bullet
        if len(price_decreases) > 15:
            html_parts.append(f"<li><em>...and {len(price_decreases) - 15} more</em></li>")
        html_parts.append("</ul>")
    
    if price_increases:
        html_parts.append("<h3>📈 Price Increases</h3><ul>")
        for change in price_increases[:15]:
            html_parts.append(f"<li>{format_change_line(change)[2:]}</li>")
        if len(price_increases) > 15:
            html_parts.append(f"<li><em>...and {len(price_increases) - 15} more</em></li>")
        html_parts.append("</ul>")
    
    if new_models:
        html_parts.append("<h3>🆕 New Models</h3><ul>")
        for change in new_models[:15]:
            html_parts.append(f"<li>{format_change_line(change)[2:]}</li>")
        if len(new_models) > 15:
            html_parts.append(f"<li><em>...and {len(new_models) - 15} more</em></li>")
        html_parts.append("</ul>")
    
    html_parts.extend([
        "<hr>",
        f"<p><a href='{WEBSITE_URL}/changelog'>View full changelog</a></p>",
        "<p><small>You're receiving this because you subscribed to LLM Price Tracker alerts.</small></p>"
    ])
    
    return subject, "\n".join(html_parts)


def send_discord(message: dict[str, Any]) -> bool:
    """
    Send message to Discord webhook.
    
    Args:
        message: Discord webhook payload
        
    Returns:
        True if successful, False otherwise
    """
    # Check both WEBHOOK_URL (user's secret name) and DISCORD_WEBHOOK_URL (spec name)
    webhook_url = os.environ.get("WEBHOOK_URL") or os.environ.get("DISCORD_WEBHOOK_URL")
    
    if not webhook_url:
        print("⚠ WEBHOOK_URL / DISCORD_WEBHOOK_URL not set, skipping Discord notification")
        return False
    
    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            response = client.post(webhook_url, json=message)
            response.raise_for_status()
            print("✓ Discord notification sent successfully")
            return True
    except httpx.HTTPError as e:
        print(f"❌ Failed to send Discord notification: {e}")
        return False


def send_slack(message: dict[str, Any]) -> bool:
    """
    Send message to Slack webhook.
    
    Args:
        message: Slack webhook payload
        
    Returns:
        True if successful, False otherwise
    """
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    
    if not webhook_url:
        print("⚠ SLACK_WEBHOOK_URL not set, skipping Slack notification")
        return False
    
    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            response = client.post(webhook_url, json=message)
            response.raise_for_status()
            print("✓ Slack notification sent successfully")
            return True
    except httpx.HTTPError as e:
        print(f"❌ Failed to send Slack notification: {e}")
        return False


def send_email(changelog: dict[str, Any]) -> bool:
    """
    Send email via Buttondown API.
    
    Args:
        changelog: Changelog data
        
    Returns:
        True if successful, False otherwise
    """
    api_key = os.environ.get("BUTTONDOWN_API_KEY")
    
    if not api_key:
        print("⚠ BUTTONDOWN_API_KEY not set, skipping email notification")
        return False
    
    subject, body = format_email(changelog)
    
    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            response = client.post(
                "https://api.buttondown.email/v1/emails",
                headers={"Authorization": f"Token {api_key}"},
                json={
                    "subject": subject,
                    "body": body,
                    "status": "published"  # Sends immediately to all subscribers
                }
            )
            response.raise_for_status()
            print("✓ Email notification sent successfully")
            return True
    except httpx.HTTPError as e:
        print(f"❌ Failed to send email notification: {e}")
        return False


def create_test_changelog() -> dict[str, Any]:
    """
    Create a dummy changelog for testing Discord webhook.
    
    Returns:
        Test changelog with sample price changes
    """
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "changes": [
            {
                "model_id": "openai/gpt-4o",
                "change_type": "price_decrease",
                "field": "input_per_million",
                "old_value": 5.00,
                "new_value": 2.50,
                "percent_change": -50.0,
                "detected_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "model_id": "anthropic/claude-3-5-sonnet",
                "change_type": "price_decrease",
                "field": "output_per_million",
                "old_value": 15.00,
                "new_value": 12.00,
                "percent_change": -20.0,
                "detected_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "model_id": "google/gemini-2-pro",
                "change_type": "new_model",
                "new_value": {
                    "input_per_million": 1.25,
                    "output_per_million": 5.00
                },
                "detected_at": datetime.now(timezone.utc).isoformat()
            }
        ],
        "summary": {
            "price_increases": 0,
            "price_decreases": 2,
            "new_models": 1,
            "removed_models": 0
        }
    }


def main() -> None:
    """
    Main entry point for the alert sender.
    
    Workflow:
    1. Load changelog/latest.json (or use test data with --test flag)
    2. Format messages for each platform
    3. Send to Discord, Slack, Email (if configured)
    
    Usage:
        python send_alerts.py          # Send real changelog alerts
        python send_alerts.py --test    # Send dummy test notification
    """
    parser = argparse.ArgumentParser(
        description="Send LLM Price Tracker alerts to Discord, Slack, and Email"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Send a dummy test notification to verify webhook configuration"
    )
    args = parser.parse_args()
    
    print("=" * 60)
    print("LLM Price Tracker - Alert Sender")
    if args.test:
        print("🧪 TEST MODE - Using dummy changelog data")
    print(f"Started at: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)
    
    # Load changelog (or use test data)
    if args.test:
        print("\n📂 Creating test changelog...")
        changelog = create_test_changelog()
        print("✓ Created test changelog with sample price changes")
    else:
        changelog_path = CHANGELOG_DIR / "latest.json"
        
        if not changelog_path.exists():
            print("⚠ No changelog found at", changelog_path)
            print("  Run detect_changes.py first to generate changelog")
            print("  Or use --test to send a test notification")
            return
        
        print("\n📂 Loading changelog...")
        changelog = load_json(changelog_path)
        
        # Check if already notified to prevent duplicate alerts
        if changelog.get("notified", False):
            print("⚠ This changelog was already notified at:", changelog.get("notified_at", "unknown"))
            print("  Skipping to avoid duplicate alerts")
            print("  (latest.json is kept for API access)")
            return
    
    changes = changelog.get("changes", [])
    summary = changelog.get("summary", {})
    
    print(f"✓ Changelog has {len(changes)} changes")
    print(f"  Summary: {summary}")
    
    if not changes:
        print("\n⚠ No changes to report, skipping notifications")
        return
    
    # Send notifications
    print("\n📤 Sending notifications...")
    
    results = {
        "discord": False,
        "slack": False,
        "email": False
    }
    
    # Discord
    discord_message = format_discord_message(changelog)
    results["discord"] = send_discord(discord_message)
    
    # Slack
    slack_message = format_slack_message(changelog)
    results["slack"] = send_slack(slack_message)
    
    # Email (skip in test mode to avoid spamming subscribers)
    if args.test:
        print("⚠ Skipping email in test mode to avoid spamming subscribers")
    else:
        results["email"] = send_email(changelog)
    
    # Summary
    print("\n" + "=" * 60)
    sent_count = sum(1 for v in results.values() if v)
    skipped_count = sum(1 for v in results.values() if not v)
    print(f"✅ Alert sending completed: {sent_count} sent, {skipped_count} skipped")
    if args.test:
        print("🧪 This was a TEST notification with dummy data")
    else:
        # Mark latest.json as notified to prevent duplicate alerts
        # This keeps the file available for API access while avoiding re-sends
        changelog_path = CHANGELOG_DIR / "latest.json"
        if sent_count > 0 and changelog_path.exists():
            changelog["notified"] = True
            changelog["notified_at"] = datetime.now(timezone.utc).isoformat()
            with open(changelog_path, "w", encoding="utf-8") as f:
                json.dump(changelog, f, indent=2)
            print("✓ Marked latest.json as notified (kept for API access)")
    print("=" * 60)


if __name__ == "__main__":
    main()
