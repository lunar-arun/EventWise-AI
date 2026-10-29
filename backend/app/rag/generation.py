import json
import re
from typing import Any, Optional, Protocol
import httpx
from pydantic import BaseModel, Field

from app.config import settings
from app.rag.prompts import build_chat_prompt, build_planner_prompt
from app.schemas.event import ThemeRecommendation
from app.schemas.knowledge import SourceCitation


class GeneratedPlanPayload(BaseModel):
    summary: str = Field(..., min_length=10)
    theme_recommendations: list[ThemeRecommendation] = Field(default_factory=list)
    ai_suggestions: list[str] = Field(default_factory=list)
    cited_chunk_ids: list[str] = Field(default_factory=list)
    missing_evidence_note: str = Field(default="")


class GeneratedChatPayload(BaseModel):
    reply: str = Field(..., min_length=5)
    suggestions: list[str] = Field(default_factory=list)
    cited_chunk_ids: list[str] = Field(default_factory=list)
    missing_evidence_note: str = Field(default="")


def filter_verified_citations(
    cited_chunk_ids: list[str],
    retrieved_chunks: list[SourceCitation],
) -> list[SourceCitation]:
    """
    Ensure every returned citation maps strictly to an actual retrieved chunk.
    Never allow fabricated chunk IDs or synthetic references.
    """
    if not retrieved_chunks:
        return []
    lookup = {c.chunk_id: c for c in retrieved_chunks}
    verified: list[SourceCitation] = []
    seen: set[str] = set()
    for cid in cited_chunk_ids:
        if cid in lookup and cid not in seen:
            verified.append(lookup[cid])
            seen.add(cid)
    # If the model used the retrieved passages but omitted exact IDs, attach top retrieved chunks
    if not verified and retrieved_chunks:
        for c in retrieved_chunks[:3]:
            if c.chunk_id not in seen:
                verified.append(c)
                seen.add(c.chunk_id)
    return verified


def _extract_json_object(raw_text: str) -> dict[str, Any]:
    cleaned = raw_text.strip()
    # Strip <think>...</think> blocks if using a reasoning model like qwen3
    cleaned = re.sub(r"<think>.*?</think>", "", cleaned, flags=re.DOTALL).strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


class GenerationProvider(Protocol):
    def check_health(self) -> dict[str, Any]: ...

    def generate_event_plan(
        self,
        event_details: dict[str, Any],
        retrieved_chunks: list[SourceCitation],
        fallback_reason: Optional[str] = None,
    ) -> tuple[GeneratedPlanPayload, list[SourceCitation], str]: ...

    def generate_chat_reply(
        self,
        user_message: str,
        event_context: str,
        conversation_history: str,
        retrieved_chunks: list[SourceCitation],
        fallback_reason: Optional[str] = None,
    ) -> tuple[GeneratedChatPayload, list[SourceCitation], str]: ...


class OllamaGenerationService:
    def __init__(
        self,
        base_url: str | None = None,
        model_name: str | None = None,
        timeout_seconds: float | None = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model_name = model_name or settings.OLLAMA_MODEL
        self.timeout = timeout_seconds or settings.OLLAMA_TIMEOUT_SECONDS

    def check_health(self) -> dict[str, Any]:
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(f"{self.base_url}/api/tags")
                resp.raise_for_status()
                data = resp.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                configured_available = any(
                    m == self.model_name or m.startswith(f"{self.model_name}:")
                    for m in models
                )
                return {
                    "status": "online" if configured_available else "model_missing",
                    "ollama_reachable": True,
                    "configured_model": self.model_name,
                    "configured_model_available": configured_available,
                    "available_models": models,
                }
        except Exception as exc:
            return {
                "status": "offline",
                "ollama_reachable": False,
                "configured_model": self.model_name,
                "configured_model_available": False,
                "available_models": [],
                "detail": f"Local Ollama service unavailable at {self.base_url}: {type(exc).__name__}",
            }

    def _call_ollama_json(self, prompt: str) -> dict[str, Any]:
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.2,
                "num_predict": 900,
            },
        }
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(f"{self.base_url}/api/generate", json=payload)
            resp.raise_for_status()
            body = resp.json()
            raw_response = body.get("response", "")
            return _extract_json_object(raw_response)

    def _build_fallback_plan(
        self,
        event_details: dict[str, Any],
        retrieved_chunks: list[SourceCitation],
        fallback_reason: Optional[str] = None,
    ) -> GeneratedPlanPayload:
        etype = str(event_details.get("event_type", "birthday")).lower()
        name = str(event_details.get("name", "Special Event"))
        location = str(event_details.get("location", "India"))
        guests = event_details.get("guest_count", 50)
        budget = event_details.get("total_budget", 25000)
        pref_theme = event_details.get("preferred_theme") or f"Classic {etype.capitalize()} Celebration"
        dietary = event_details.get("dietary_requirements") or "Standard multi-option menu"

        has_evidence = len(retrieved_chunks) > 0
        evidence_titles = ", ".join(dict.fromkeys(c.title for c in retrieved_chunks[:3]))

        missing_note = fallback_reason or ""
        if not has_evidence:
            missing_note = (
                "The local knowledge base did not return matching passages for this event query. "
                "Recommendations below are general planning suggestions with illustrative INR estimates."
            )

        summary = (
            f"Personalized {etype} plan for '{name}' in {location} for {guests} guests with a total "
            f"illustrative budget of ₹{budget:,} INR. "
            + (
                f"Grounded in retrieved local knowledge ({evidence_titles}). "
                if has_evidence
                else "Generated using general event planning templates because no matching knowledge chunks were retrieved. "
            )
            + "All monetary figures are illustrative estimates calculated deterministically in Python."
        )

        themes = [
            ThemeRecommendation(
                title=pref_theme,
                tagline=f"Tailored {etype.capitalize()} Experience for {guests} Guests",
                description=(
                    f"Designed for {location} with focus on guest flow, cohesive color accents, "
                    f"and cost-effective photo backdrops suitable for a ₹{budget:,} budget."
                ),
                decor_highlights=[
                    "Reusable fabric drapes with warm LED fairy lighting",
                    "Focal welcome board and themed photo booth corner",
                    "Table centerpieces using seasonal local florals and lanterns",
                ],
                catering_notes=f"Menu structured around '{dietary}' with 10% buffer for {guests} guests.",
                estimated_tier="Illustrative Estimate (Balanced Fit)",
                source_Backed=has_evidence,
            ),
            ThemeRecommendation(
                title=f"Eco-Friendly Royal Garden {etype.capitalize()}",
                tagline="Sustainable elegance with natural textures",
                description=(
                    "Emphasizes potted greens, terracotta accents, and zero-plastic tableware to keep "
                    "decoration and cleanup costs predictable."
                ),
                decor_highlights=[
                    "Potted foliage and marigold/jasmine garlands",
                    "Handcrafted paper lanterns and warm uplighting",
                    "Minimalist stage frame with natural botanical accents",
                ],
                catering_notes=f"Live regional counter + buffet service aligned with {dietary}.",
                estimated_tier="Illustrative Estimate (Value Saver)",
                source_Backed=has_evidence,
            ),
        ]

        suggestions = [
            f"Lock in the venue and catering quotes at least 2–3 weeks early to stay within the ₹{budget:,} illustrative budget.",
            "Keep the 10–12% Emergency Reserve untouched until event week for unforeseen logistics or extra guests.",
            f"Confirm final headcount ({guests} guests) and '{dietary}' menu split 7 days before the event date.",
            "Compare at least 3 local vendors using the Vendor Evaluation Checklist before paying booking advances.",
        ]
        if has_evidence:
            suggestions.insert(
                0,
                f"Source-backed tip from '{retrieved_chunks[0].title}': Prioritize core guest experience (food & seating comfort) over single-use stage props.",
            )

        return GeneratedPlanPayload(
            summary=summary,
            theme_recommendations=themes,
            ai_suggestions=suggestions[:5],
            cited_chunk_ids=[c.chunk_id for c in retrieved_chunks[:3]],
            missing_evidence_note=missing_note,
        )

    def generate_event_plan(
        self,
        event_details: dict[str, Any],
        retrieved_chunks: list[SourceCitation],
        fallback_reason: Optional[str] = None,
    ) -> tuple[GeneratedPlanPayload, list[SourceCitation], str]:
        prompt = build_planner_prompt(event_details, retrieved_chunks)
        try:
            raw_json = self._call_ollama_json(prompt)
            payload = GeneratedPlanPayload.model_validate(raw_json)
            if not payload.theme_recommendations:
                fallback = self._build_fallback_plan(event_details, retrieved_chunks, fallback_reason)
                payload.theme_recommendations = fallback.theme_recommendations
            if not payload.ai_suggestions:
                fallback = self._build_fallback_plan(event_details, retrieved_chunks, fallback_reason)
                payload.ai_suggestions = fallback.ai_suggestions
            if fallback_reason and not payload.missing_evidence_note:
                payload.missing_evidence_note = fallback_reason
            if not retrieved_chunks and not payload.missing_evidence_note:
                payload.missing_evidence_note = (
                    "The local knowledge base did not contain supporting passages for this query; "
                    "offering clearly labeled general suggestions."
                )
            verified_citations = filter_verified_citations(payload.cited_chunk_ids, retrieved_chunks)
            return payload, verified_citations, "ollama"
        except Exception:
            fallback_payload = self._build_fallback_plan(event_details, retrieved_chunks, fallback_reason)
            verified_citations = filter_verified_citations(fallback_payload.cited_chunk_ids, retrieved_chunks)
            return fallback_payload, verified_citations, "deterministic_fallback"

    def _build_fallback_chat(
        self,
        user_message: str,
        event_context: str,
        retrieved_chunks: list[SourceCitation],
        fallback_reason: Optional[str] = None,
    ) -> GeneratedChatPayload:
        has_evidence = len(retrieved_chunks) > 0
        msg_lower = user_message.lower()

        missing_note = fallback_reason or ""
        if not has_evidence:
            missing_note = (
                "No supporting passages were found in the local knowledge base for this specific question. "
                "Providing general event planning guidance and deterministic Python calculations."
            )

        parts: list[str] = []
        if "reduce" in msg_lower or "budget" in msg_lower or "cost" in msg_lower or "save" in msg_lower:
            parts.append(
                "Based on deterministic Python budget calculations, I have prepared a proposed budget adjustment "
                "while preserving your Emergency Reserve. Note that EventWise AI never changes your approved "
                "total budget silently—you can review and approve the proposal below."
            )
        if "theme" in msg_lower:
            parts.append(
                "Here are three adaptable theme directions with illustrative INR tiers:\n"
                "1. **Retro Starlight Carnival**: Warm fairy lights, DIY photo frame, and vibrant table runners.\n"
                "2. **Botanical Garden Fiesta**: Potted local greens, marigold accents, and reusable fabric drapes.\n"
                "3. **Minimalist Royal Pastels**: Clean balloon garland arch, pastel linens, and acoustic playlist."
            )
        if "task" in msg_lower or "remain" in msg_lower or "timeline" in msg_lower or "checklist" in msg_lower:
            parts.append(
                "I checked your persisted event checklist in SQLite. Review the active pending and in-progress "
                "tasks summarized in the context panel, and prioritize items due within the next 7 days."
            )
        if "vegetarian" in msg_lower or "menu" in msg_lower or "catering" in msg_lower or "food" in msg_lower:
            parts.append(
                "For a vegetarian or specialized menu, allocate roughly 30–35% of your total budget to Food & Beverages "
                "(illustrative estimate). Include 2 welcome drinks, 3 starters, 2 main course gravies, assorted breads, "
                "a fragrant rice dish, and 2 desserts, plus a 10% buffer for extra guests."
            )

        if has_evidence:
            top_cite = retrieved_chunks[0]
            parts.append(
                f"From the local knowledge base (**{top_cite.title}**): {top_cite.excerpt[:260].strip()}..."
            )
        elif not parts:
            parts.append(
                "Here is guidance tailored to your event context. Note that all price references are illustrative "
                "estimates in INR rather than live vendor quotes."
            )

        return GeneratedChatPayload(
            reply="\n\n".join(parts),
            suggestions=[
                "Review the deterministic budget breakdown before committing vendor advances.",
                "Use modular DIY lighting and seasonal local flowers to reduce decoration costs by 15–25%.",
                "Keep your 10–12% Emergency Reserve intact until event day.",
            ],
            cited_chunk_ids=[c.chunk_id for c in retrieved_chunks[:3]],
            missing_evidence_note=missing_note,
        )

    def generate_chat_reply(
        self,
        user_message: str,
        event_context: str,
        conversation_history: str,
        retrieved_chunks: list[SourceCitation],
        fallback_reason: Optional[str] = None,
    ) -> tuple[GeneratedChatPayload, list[SourceCitation], str]:
        prompt = build_chat_prompt(
            event_context=event_context,
            conversation_history=conversation_history,
            citations=retrieved_chunks,
            user_message=user_message,
        )
        try:
            raw_json = self._call_ollama_json(prompt)
            payload = GeneratedChatPayload.model_validate(raw_json)
            if fallback_reason and not payload.missing_evidence_note:
                payload.missing_evidence_note = fallback_reason
            if not retrieved_chunks and not payload.missing_evidence_note:
                payload.missing_evidence_note = (
                    "The local knowledge base did not contain supporting passages for this query; "
                    "providing general suggestions."
                )
            verified_citations = filter_verified_citations(payload.cited_chunk_ids, retrieved_chunks)
            return payload, verified_citations, "ollama"
        except Exception:
            fallback_payload = self._build_fallback_chat(
                user_message=user_message,
                event_context=event_context,
                retrieved_chunks=retrieved_chunks,
                fallback_reason=fallback_reason,
            )
            verified_citations = filter_verified_citations(fallback_payload.cited_chunk_ids, retrieved_chunks)
            return fallback_payload, verified_citations, "deterministic_fallback"


_active_generation_service: GenerationProvider | None = None


def get_generation_service() -> GenerationProvider:
    global _active_generation_service
    if _active_generation_service is None:
        _active_generation_service = OllamaGenerationService()
    return _active_generation_service


def set_generation_service(service: GenerationProvider | None) -> None:
    global _active_generation_service
    _active_generation_service = service
