"""Optional image generation and deterministic fallback cards."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from github_insight.config import AppConfig
from github_insight.models import InsightRecord, RunMetadata
from github_insight.utils import ensure_parent, safe_slug


CARD_SIZE = (1200, 630)


def _font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def _wrap(text: str, max_chars: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        if sum(len(item) for item in current) + len(current) + len(word) > max_chars:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines[:4]


def _draw_card(path: Path, title: str, subtitle: str, score: float, action: str) -> None:
    image = Image.new("RGB", CARD_SIZE, "#f8fafc")
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, 0, CARD_SIZE[0], 112], fill="#0f172a")
    draw.text((48, 34), "GitHub Insight", fill="#ffffff", font=_font(34))
    draw.rounded_rectangle([48, 150, 1152, 560], radius=22, fill="#ffffff", outline="#cbd5e1", width=2)
    draw.text((82, 188), title[:72], fill="#0f172a", font=_font(38))
    y = 248
    for line in _wrap(subtitle, 82):
        draw.text((82, y), line, fill="#334155", font=_font(24))
        y += 34
    draw.rounded_rectangle([82, 430, 330, 506], radius=16, fill="#0f766e")
    draw.text((108, 452), f"Score {score:.2f}", fill="#ffffff", font=_font(28))
    draw.text((370, 452), f"Action: {action}", fill="#0f172a", font=_font(24))
    ensure_parent(path)
    image.save(path)


def _metadata(
    run: RunMetadata,
    record: InsightRecord | None,
    model: str,
    prompt: str,
    asset_path: Path | None,
    status: str,
    error: str | None = None,
) -> dict[str, Any]:
    source_facts = {}
    full_name = "daily-hero"
    alt_text = "AI-generated style fallback card for the GitHub Insight daily brief."
    if record:
        full_name = record.full_name
        source_facts = {
            "full_name": record.full_name,
            "score": record.overall_insight_score,
            "primary_audience": record.primary_audience,
            "recommended_action": record.recommended_action,
            "risk_flags": record.risk_flags,
        }
        alt_text = f"Fallback visual card for {record.full_name}, score {record.overall_insight_score:.2f}."
    return {
        "date": run.date,
        "full_name": full_name,
        "model": model,
        "prompt": prompt,
        "source_facts": source_facts,
        "alt_text": alt_text,
        "generated_at": run.generated_at,
        "status": status,
        "asset_path": asset_path.as_posix() if asset_path else "",
        "error": error,
    }


def create_fallback_project_card(
    output_root: Path,
    run: RunMetadata,
    record: InsightRecord,
    model: str = "gpt-image-2",
) -> tuple[Path, Path]:
    slug = safe_slug(record.full_name)
    image_path = output_root / "assets" / "images" / run.date / f"{slug}.png"
    prompt_path = output_root / "assets" / "images" / run.date / f"{slug}.json"
    prompt = (
        "For a GitHub repository useful to its selected audience, create a professional editorial data product visual; "
        "no logos, no fake UI screenshots, no readable long text."
    )
    _draw_card(image_path, record.full_name, record.one_sentence_summary, record.overall_insight_score, record.recommended_action)
    metadata = _metadata(run, record, model, prompt, image_path.relative_to(output_root), "fallback")
    ensure_parent(prompt_path).write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    return image_path, prompt_path


def create_daily_hero_fallback(output_root: Path, run: RunMetadata, records: list[InsightRecord], model: str) -> tuple[Path, Path]:
    image_path = output_root / "assets" / "images" / run.date / "daily-hero.png"
    prompt_path = output_root / "assets" / "images" / run.date / "daily-hero.json"
    top = records[0].full_name if records else "No selected project"
    prompt = "Editorial visualization of an open-source intelligence dashboard; no logos; no readable text."
    _draw_card(image_path, f"Daily Radar - {run.date}", f"Top project: {top}", records[0].overall_insight_score if records else 0, "Daily review")
    metadata = _metadata(run, None, model, prompt, image_path.relative_to(output_root), "fallback")
    ensure_parent(prompt_path).write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    return image_path, prompt_path


def apply_optional_images(output_root: Path, run: RunMetadata, records: list[InsightRecord], config: AppConfig) -> list[Path]:
    if not config.enable_image_generation:
        return []
    generated: list[Path] = []
    openai_key = os.getenv("OPENAI_API_KEY")
    status_note = "fallback" if not openai_key else "fallback"
    # The core pipeline is deterministic. GPT Image generation can be added later behind the same metadata contract.
    hero_image, hero_meta = create_daily_hero_fallback(output_root, run, records, config.image_model)
    generated.extend([hero_image, hero_meta])
    for record in records[: config.image_top_n]:
        image_path, prompt_path = create_fallback_project_card(output_root, run, record, config.image_model)
        record.image_asset_path = image_path.relative_to(output_root).as_posix()
        record.image_prompt_path = prompt_path.relative_to(output_root).as_posix()
        generated.extend([image_path, prompt_path])
    _ = status_note
    return generated
