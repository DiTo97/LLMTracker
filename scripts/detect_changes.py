"""
LLM Price Tracker - Change Detection Module

Purpose: Compare current prices to previous snapshot and generate changelog.

Input:
- data/current/prices.json (new)
- data/history/YYYY/MM/DD.json (previous, find most recent)

Output:
- data/changelog/latest.json
- data/changelog/YYYY-MM-DD.json
- Copies current prices to data/history/YYYY/MM/DD.json

Returns: True if changes detected, False otherwise
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CURRENT_DIR = DATA_DIR / "current"
HISTORY_DIR = DATA_DIR / "history"
CHANGELOG_DIR = DATA_DIR / "changelog"


class ChangeType(str, Enum):
    """Types of changes that can be detected."""
    PRICE_INCREASE = "price_increase"
    PRICE_DECREASE = "price_decrease"
    NEW_MODEL = "new_model"
    REMOVED_MODEL = "removed_model"
    CONTEXT_CHANGE = "context_change"
    CAPABILITY_CHANGE = "capability_change"
    CACHE_PRICE_CHANGE = "cache_price_change"


class Change(BaseModel):
    """A single price or model change."""
    model_id: str
    change_type: ChangeType
    field: Optional[str] = None
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    percent_change: Optional[float] = None
    detected_at: str


class ChangelogSummary(BaseModel):
    """Summary statistics for a changelog."""
    price_increases: int = 0
    price_decreases: int = 0
    new_models: int = 0
    removed_models: int = 0
    cache_price_changes: int = 0
    other_changes: int = 0


class Changelog(BaseModel):
    """Complete changelog for a price update."""
    generated_at: str
    changes: list[Change]
    summary: ChangelogSummary


def load_json(filepath: Path) -> dict[str, Any]:
    """Load a JSON file and return its contents."""
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filepath: Path, data: Any) -> None:
    """Save data to a JSON file with pretty formatting."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved: {filepath}")


def find_previous_snapshot() -> Optional[Path]:
    """
    Find most recent file in data/history/.
    
    Traverses the history directory structure (YYYY/MM/DD.json) to find
    the most recent snapshot file.
    
    Returns:
        Path to most recent snapshot, or None if no history exists
    """
    if not HISTORY_DIR.exists():
        print("⚠ No history directory found - this appears to be the first run")
        return None
    
    # Find all JSON files in history
    json_files = list(HISTORY_DIR.rglob("*.json"))
    
    if not json_files:
        print("⚠ No history files found - this appears to be the first run")
        return None
    
    # Sort by path (which is date-based) and get most recent
    # Path format: YYYY/MM/DD.json
    json_files.sort(reverse=True)
    
    most_recent = json_files[0]
    print(f"✓ Found previous snapshot: {most_recent}")
    
    return most_recent


def calculate_percent_change(old_value: float, new_value: float) -> float:
    """
    Calculate percent change between two values.
    
    Args:
        old_value: Previous value
        new_value: Current value
        
    Returns:
        Percent change (positive = increase, negative = decrease)
    """
    if old_value == 0:
        if new_value == 0:
            return 0.0
        return 100.0  # From 0 to any value is 100% increase
    
    return round(((new_value - old_value) / old_value) * 100, 2)


def detect_price_changes(
    old_data: dict[str, Any],
    new_data: dict[str, Any]
) -> list[Change]:
    """
    Compare each model's pricing between old and new data.
    
    Detects:
    - price_increase: Input or output price went up
    - price_decrease: Input or output price went down
    - cache_price_change: Cache read/write pricing changed
    - new_model: Model exists in new but not old
    - removed_model: Model exists in old but not new
    
    Args:
        old_data: Previous prices.json content
        new_data: Current prices.json content
        
    Returns:
        List of detected changes
    """
    changes: list[Change] = []
    now = datetime.now(timezone.utc).isoformat()
    
    old_models = old_data.get("models", {})
    new_models = new_data.get("models", {})
    
    old_model_ids = set(old_models.keys())
    new_model_ids = set(new_models.keys())
    
    # Detect new models
    for model_id in new_model_ids - old_model_ids:
        new_model = new_models[model_id]
        pricing = new_model.get("pricing", {})
        changes.append(Change(
            model_id=model_id,
            change_type=ChangeType.NEW_MODEL,
            field="model",
            old_value=None,
            new_value={
                "input_per_million": pricing.get("input_per_million"),
                "output_per_million": pricing.get("output_per_million"),
                "cache_read_per_million": pricing.get("cache_read_per_million"),
                "cache_creation_per_million": pricing.get("cache_creation_per_million"),
            },
            detected_at=now
        ))
    
    # Detect removed models
    for model_id in old_model_ids - new_model_ids:
        old_model = old_models[model_id]
        pricing = old_model.get("pricing", {})
        changes.append(Change(
            model_id=model_id,
            change_type=ChangeType.REMOVED_MODEL,
            field="model",
            old_value={
                "input_per_million": pricing.get("input_per_million"),
                "output_per_million": pricing.get("output_per_million"),
                "cache_read_per_million": pricing.get("cache_read_per_million"),
                "cache_creation_per_million": pricing.get("cache_creation_per_million"),
            },
            new_value=None,
            detected_at=now
        ))
    
    # Detect price changes for existing models
    for model_id in old_model_ids & new_model_ids:
        old_model = old_models[model_id]
        new_model = new_models[model_id]
        
        old_pricing = old_model.get("pricing", {})
        new_pricing = new_model.get("pricing", {})
        
        # Check input price
        old_input = old_pricing.get("input_per_million", 0)
        new_input = new_pricing.get("input_per_million", 0)
        
        if old_input != new_input:
            percent = calculate_percent_change(old_input, new_input)
            change_type = ChangeType.PRICE_INCREASE if new_input > old_input else ChangeType.PRICE_DECREASE
            changes.append(Change(
                model_id=model_id,
                change_type=change_type,
                field="input_per_million",
                old_value=old_input,
                new_value=new_input,
                percent_change=percent,
                detected_at=now
            ))
        
        # Check output price
        old_output = old_pricing.get("output_per_million", 0)
        new_output = new_pricing.get("output_per_million", 0)
        
        if old_output != new_output:
            percent = calculate_percent_change(old_output, new_output)
            change_type = ChangeType.PRICE_INCREASE if new_output > old_output else ChangeType.PRICE_DECREASE
            changes.append(Change(
                model_id=model_id,
                change_type=change_type,
                field="output_per_million",
                old_value=old_output,
                new_value=new_output,
                percent_change=percent,
                detected_at=now
            ))
        
        # Check cache read price
        old_cache_read = old_pricing.get("cache_read_per_million")
        new_cache_read = new_pricing.get("cache_read_per_million")
        
        if old_cache_read != new_cache_read and (old_cache_read is not None or new_cache_read is not None):
            old_val = old_cache_read or 0
            new_val = new_cache_read or 0
            percent = calculate_percent_change(old_val, new_val) if old_val > 0 else None
            changes.append(Change(
                model_id=model_id,
                change_type=ChangeType.CACHE_PRICE_CHANGE,
                field="cache_read_per_million",
                old_value=old_cache_read,
                new_value=new_cache_read,
                percent_change=percent,
                detected_at=now
            ))
        
        # Check cache creation price
        old_cache_creation = old_pricing.get("cache_creation_per_million")
        new_cache_creation = new_pricing.get("cache_creation_per_million")
        
        if old_cache_creation != new_cache_creation and (old_cache_creation is not None or new_cache_creation is not None):
            old_val = old_cache_creation or 0
            new_val = new_cache_creation or 0
            percent = calculate_percent_change(old_val, new_val) if old_val > 0 else None
            changes.append(Change(
                model_id=model_id,
                change_type=ChangeType.CACHE_PRICE_CHANGE,
                field="cache_creation_per_million",
                old_value=old_cache_creation,
                new_value=new_cache_creation,
                percent_change=percent,
                detected_at=now
            ))
        
        # Check context window changes
        old_context = old_model.get("context_window", 0)
        new_context = new_model.get("context_window", 0)
        
        if old_context != new_context and (old_context > 0 or new_context > 0):
            changes.append(Change(
                model_id=model_id,
                change_type=ChangeType.CONTEXT_CHANGE,
                field="context_window",
                old_value=old_context,
                new_value=new_context,
                percent_change=calculate_percent_change(old_context, new_context) if old_context > 0 else None,
                detected_at=now
            ))
    
    return changes


def generate_changelog(changes: list[Change]) -> Changelog:
    """
    Create changelog object with summary statistics.
    
    Args:
        changes: List of detected changes
        
    Returns:
        Complete changelog with summary
    """
    summary = ChangelogSummary()
    
    for change in changes:
        if change.change_type == ChangeType.PRICE_INCREASE:
            summary.price_increases += 1
        elif change.change_type == ChangeType.PRICE_DECREASE:
            summary.price_decreases += 1
        elif change.change_type == ChangeType.NEW_MODEL:
            summary.new_models += 1
        elif change.change_type == ChangeType.REMOVED_MODEL:
            summary.removed_models += 1
        elif change.change_type == ChangeType.CACHE_PRICE_CHANGE:
            summary.cache_price_changes += 1
        else:
            summary.other_changes += 1
    
    return Changelog(
        generated_at=datetime.now(timezone.utc).isoformat(),
        changes=changes,
        summary=summary
    )


def save_history_snapshot(prices_data: dict[str, Any]) -> Path:
    """
    Save current prices to history directory.
    
    File is saved as: data/history/YYYY/MM/DD.json
    
    Args:
        prices_data: Current prices.json content
        
    Returns:
        Path to saved file
    """
    now = datetime.now(timezone.utc)
    year = str(now.year)
    month = f"{now.month:02d}"
    day = f"{now.day:02d}"
    
    history_path = HISTORY_DIR / year / month / f"{day}.json"
    save_json(history_path, prices_data)
    
    return history_path


def main() -> bool:
    """
    Main entry point for change detection.
    
    Workflow:
    1. Load current prices.json
    2. Find most recent historical snapshot
    3. Compare and detect changes
    4. If changes found, save changelog
    5. Save current prices to history
    
    Returns:
        True if changes were detected, False otherwise
    """
    print("=" * 60)
    print("LLM Price Tracker - Change Detection")
    print(f"Started at: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)
    
    # Load current data
    print("\n📂 Loading current prices...")
    current_path = CURRENT_DIR / "prices.json"
    
    if not current_path.exists():
        print("❌ No current prices.json found. Run normalize.py first.")
        return False
    
    current_data = load_json(current_path)
    print(f"✓ Loaded current prices: {current_data.get('metadata', {}).get('total_models', 0)} models")
    
    # Find previous snapshot
    print("\n🔍 Looking for previous snapshot...")
    previous_path = find_previous_snapshot()
    
    has_changes = False
    
    if previous_path is None:
        # First run - no changes to detect
        print("ℹ First run detected - no changes to compare")
    else:
        # Load previous and detect changes
        previous_data = load_json(previous_path)
        print(f"✓ Loaded previous: {previous_data.get('metadata', {}).get('total_models', 0)} models")
        
        print("\n🔄 Detecting changes...")
        changes = detect_price_changes(previous_data, current_data)
        
        if changes:
            has_changes = True
            changelog = generate_changelog(changes)
            
            print(f"\n📊 Changes detected:")
            print(f"   Price increases: {changelog.summary.price_increases}")
            print(f"   Price decreases: {changelog.summary.price_decreases}")
            print(f"   Cache price changes: {changelog.summary.cache_price_changes}")
            print(f"   New models: {changelog.summary.new_models}")
            print(f"   Removed models: {changelog.summary.removed_models}")
            print(f"   Other changes: {changelog.summary.other_changes}")
            
            # Save changelog
            print("\n💾 Saving changelog...")
            CHANGELOG_DIR.mkdir(parents=True, exist_ok=True)
            
            changelog_dict = changelog.model_dump()
            
            # Convert enum values to strings for JSON serialization
            for change in changelog_dict["changes"]:
                if isinstance(change["change_type"], ChangeType):
                    change["change_type"] = change["change_type"].value
            
            save_json(CHANGELOG_DIR / "latest.json", changelog_dict)
            
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            save_json(CHANGELOG_DIR / f"{today}.json", changelog_dict)
        else:
            print("✓ No price changes detected")
    
    # Save current to history
    print("\n📁 Saving to history...")
    history_path = save_history_snapshot(current_data)
    
    print("\n" + "=" * 60)
    if has_changes:
        print("✅ Change detection completed - CHANGES FOUND!")
    else:
        print("✅ Change detection completed - no changes")
    print("=" * 60)
    
    return has_changes


if __name__ == "__main__":
    result = main()
    # Exit with code 0 if changes detected (for GitHub Actions to continue with alerts)
    # This is inverted because we want to trigger alerts when changes exist
    sys.exit(0 if result else 0)  # Always exit 0 to not fail the workflow
