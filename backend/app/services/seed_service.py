from datetime import date, timedelta
from pathlib import Path
from sqlalchemy.orm import Session

from app.config import settings
from app.database.models import EventModel, ExpenseModel, KnowledgeDocumentModel
from app.rag.ingestion import get_ingestion_service
from app.schemas.event import EventCreate
from app.services.event_service import EventService

SAMPLE_METADATA_MAP: dict[str, dict[str, str]] = {
    "01_birthday_planning_guide.txt": {
        "title": "Birthday Party Planning Guidance (Illustrative ₹25,000 Reference)",
        "event_type": "birthday",
        "category": "planning",
        "location": "Chennai / General India",
        "source_label": "Curated EventWise Birthday Guide (Illustrative)",
    },
    "02_wedding_preparation_checklist.txt": {
        "title": "Wedding Preparation Master Checklist (200 Guests Reference)",
        "event_type": "wedding",
        "category": "checklist",
        "location": "South India / General India",
        "source_label": "Curated EventWise Wedding Handbook (Illustrative)",
    },
    "03_community_event_planning_guide.txt": {
        "title": "Community Event Planning & Logistics Guide",
        "event_type": "community",
        "category": "planning",
        "location": "General India",
        "source_label": "Curated EventWise Community Guide (Illustrative)",
    },
    "04_budget_allocation_templates.json": {
        "title": "Standard Event Budget Templates & Cost Reduction Rules",
        "event_type": "general",
        "category": "budget",
        "location": "General India",
        "source_label": "Curated EventWise Budget Templates (Illustrative INR)",
    },
    "05_event_timelines_and_milestones.txt": {
        "title": "Event Timelines & Relative Milestone Scheduling Rules",
        "event_type": "general",
        "category": "timeline",
        "location": "General India",
        "source_label": "Curated EventWise Timeline Playbook",
    },
    "06_sustainable_decoration_ideas.txt": {
        "title": "Sustainable & Budget-Friendly Decoration Ideas",
        "event_type": "general",
        "category": "decoration",
        "location": "General India",
        "source_label": "Curated EventWise Decor Studio Guide (Illustrative)",
    },
    "07_catering_and_dietary_planning.txt": {
        "title": "Catering & Pure Vegetarian Dietary Menu Planning Guide",
        "event_type": "general",
        "category": "catering",
        "location": "Chennai / General India",
        "source_label": "Curated EventWise Catering Reference (Illustrative)",
    },
    "08_vendor_evaluation_checklist.txt": {
        "title": "Vendor Evaluation & Booking Verification Checklist",
        "event_type": "general",
        "category": "vendors",
        "location": "General India",
        "source_label": "Curated EventWise Vendor Due-Diligence Guide",
    },
    "09_illustrative_sample_costs_inr.csv": {
        "title": "Illustrative Sample Event Costs Dataset (Synthetic INR)",
        "event_type": "general",
        "category": "costs",
        "location": "Chennai / General India",
        "source_label": "Synthetic Illustrative Cost Dataset (Not Verified Market Quotes)",
    },
}


def seed_initial_data(db: Session) -> dict[str, int]:
    """
    Seed the curated initial knowledge base and a clearly labeled illustrative sample event
    if the database is empty.
    """
    sample_dir = Path(settings.SAMPLE_DATA_DIRECTORY)
    ingestion = get_ingestion_service()
    seeded_docs = 0

    existing_docs = db.query(KnowledgeDocumentModel).count()
    if existing_docs == 0 and sample_dir.exists():
        for file_path in sorted(sample_dir.iterdir()):
            if not file_path.is_file():
                continue
            meta = SAMPLE_METADATA_MAP.get(
                file_path.name,
                {
                    "title": file_path.stem.replace("_", " ").title(),
                    "event_type": "general",
                    "category": "general",
                    "location": "General India",
                    "source_label": "Curated EventWise Guide (Illustrative)",
                },
            )
            try:
                ingestion.ingest_file_bytes(
                    db=db,
                    filename=file_path.name,
                    content_bytes=file_path.read_bytes(),
                    title=meta["title"],
                    event_type=meta["event_type"],
                    category=meta["category"],
                    location=meta["location"],
                    source_label=meta["source_label"],
                    is_illustrative=True,
                    save_to_disk=False,
                )
                seeded_docs += 1
            except Exception:
                pass

    seeded_events = 0
    existing_events = db.query(EventModel).count()
    if existing_events == 0:
        sample_date = (date.today() + timedelta(days=28)).isoformat()
        sample_create = EventCreate(
            name="Star Kingdom 21st Birthday Bash (Illustrative Sample)",
            event_type="birthday",
            location="Chennai",
            total_budget=25000,
            guest_count=50,
            event_date=sample_date,
            preferred_theme="Retro Starlight Adventure",
            dietary_requirements="Pure Vegetarian Buffet with Live Chaat Counter",
            additional_preferences=(
                "Use reusable fabric drapes, warm LED fairy lights, and preserve the ₹3,000 emergency reserve."
            ),
            generate_initial_plan=False,
        )
        created_detail = EventService.create_event(db, sample_create)
        ev_model = db.query(EventModel).filter(EventModel.id == created_detail.id).first()
        if ev_model:
            # Populate deterministic grounded summary & citations without blocking startup on LLM latency
            retrieved, _, _ = ingestion.retrieval.retrieve(
                query="birthday planning Chennai 25000 INR vegetarian decoration",
                event_type="birthday",
                location="Chennai",
            )
            ev_model.summary = (
                "Illustrative sample birthday plan for 50 guests in Chennai with a ₹25,000 INR budget. "
                "Categories follow the standard ₹25,000 birthday template (Venue ₹5,000, Food ₹8,000, "
                "Decoration ₹3,000, Cake ₹2,000, Entertainment ₹2,000, Miscellaneous ₹2,000, Emergency reserve ₹3,000)."
            )
            ev_model.theme_recommendations = [
                {
                    "title": "Retro Starlight Adventure",
                    "tagline": "Playful Star Kingdom palette with warm LED lights",
                    "description": (
                        "Combines sky-blue and coin-gold balloon clusters with reusable fabric drapes "
                        "and a pixel-art welcome sign suitable for 50 guests."
                    ),
                    "decor_highlights": [
                        "Reusable sky-blue and gold backdrop with 300-LED curtain lights",
                        "Question-block inspired photo booth prop table",
                        "Seasonal marigold and lantern table accents",
                    ],
                    "catering_notes": "Pure vegetarian buffet with welcome lime mint cooler, paneer starter, live chaat, main course, and dessert.",
                    "estimated_tier": "Illustrative Estimate (Fits ₹25,000 Budget)",
                    "source_Backed": True,
                }
            ]
            ev_model.ai_suggestions = [
                "Lock the mini party hall slot 2–3 weeks before the event date to stay within the ₹5,000 illustrative venue allocation.",
                "Confirm a 10% plate buffer with the vegetarian caterer while keeping total food cost within ₹8,000.",
                "Use reusable LED curtain lights and seasonal local flowers to stay within the ₹3,000 decoration allocation.",
                "Keep the ₹3,000 Emergency Reserve untouched until event week.",
            ]
            ev_model.citations = [c.model_dump() for c in retrieved[:3]]
            ev_model.generation_mode = "seeded_illustrative_sample"

            # Mark first milestone task completed and second in_progress to showcase quest progress
            tasks_sorted = sorted(list(ev_model.tasks or []), key=lambda t: (t.due_date, t.id or 0))
            if len(tasks_sorted) >= 1:
                tasks_sorted[0].status = "completed"
            if len(tasks_sorted) >= 2:
                tasks_sorted[1].status = "in_progress"

            # Add one illustrative recorded expense
            sample_expense = ExpenseModel(
                event_id=ev_model.id,
                category_name="Venue",
                title="Party Hall Booking Advance (Illustrative Sample)",
                amount=2000,
                incurred_date=date.today().isoformat(),
                notes="Illustrative 40% booking advance for ₹5,000 venue allocation.",
            )
            db.add(sample_expense)
            db.commit()
            seeded_events += 1

    return {"seeded_documents": seeded_docs, "seeded_events": seeded_events}
