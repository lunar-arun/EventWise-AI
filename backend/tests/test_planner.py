from app.rag.generation import OllamaGenerationService, set_generation_service
from app.services.seed_service import seed_initial_data


def test_full_api_event_lifecycle_planner_chat_and_knowledge(test_env):
    client = test_env["client"]
    db = test_env["db"]

    # 1. Seed initial knowledge base and sample event
    seed_stats = seed_initial_data(db)
    assert seed_stats["seeded_documents"] >= 5

    # 2. Health check endpoints
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["local_only"] is True

    llm_health = client.get("/api/health/llm")
    assert llm_health.status_code == 200
    assert "configured_model" in llm_health.json()

    # 3. Create a new Birthday event via POST /api/events
    create_resp = client.post(
        "/api/events",
        json={
            "name": "Aarav's 10th Super Star Birthday",
            "event_type": "birthday",
            "location": "Chennai",
            "total_budget": 25000,
            "guest_count": 50,
            "event_date": "2027-08-20",
            "preferred_theme": "Retro Starlight Adventure",
            "dietary_requirements": "Pure Vegetarian",
            "additional_preferences": "Include DIY photo booth and preserve emergency reserve",
            "generate_initial_plan": True,
        },
    )
    assert create_resp.status_code == 201
    event_data = create_resp.json()
    event_id = event_data["id"]
    assert event_data["budget"]["total_budget"] == 25000
    assert event_data["budget"]["planned_spending"] == 25000
    assert event_data["budget"]["emergency_reserve"] == 3000
    assert len(event_data["tasks"]) == 6
    assert len(event_data["citations"]) >= 1

    # 4. Verify invalid input is rejected with 422
    bad_resp = client.post(
        "/api/events",
        json={
            "name": "Invalid Event",
            "event_type": "invalid_type",
            "location": "Chennai",
            "total_budget": -100,
            "guest_count": 0,
            "event_date": "not-a-date",
        },
    )
    assert bad_resp.status_code == 422

    # 5. Ask follow-up question in Chatbot: "Reduce my event budget by ₹5,000"
    chat_resp = client.post(
        "/api/chat",
        json={
            "message": "Reduce my event budget by ₹5,000 and keep my emergency reserve safe.",
            "event_id": event_id,
        },
    )
    assert chat_resp.status_code == 200
    chat_body = chat_resp.json()
    assert chat_body["proposed_changes"] is not None
    assert chat_body["proposed_changes"]["current_total_budget"] == 25000
    assert chat_body["proposed_changes"]["proposed_total_budget"] == 20000
    assert chat_body["proposed_changes"]["requires_user_approval"] is True

    # Confirm the chatbot did NOT silently mutate the persisted event budget in SQLite!
    budget_check = client.get(f"/api/events/{event_id}/budget")
    assert budget_check.status_code == 200
    assert budget_check.json()["total_budget"] == 25000

    # 6. Apply the user-approved proposal via PUT /api/events/{event_id}/budget
    apply_resp = client.put(
        f"/api/events/{event_id}/budget",
        json={
            "total_budget": 20000,
            "user_approved_total_change": True,
            "categories": chat_body["proposed_changes"]["proposed_categories"],
        },
    )
    assert apply_resp.status_code == 200
    assert apply_resp.json()["total_budget"] == 20000
    assert apply_resp.json()["planned_spending"] == 20000

    # 7. Dashboard summary reflects real persisted data
    dash_resp = client.get("/api/dashboard")
    assert dash_resp.status_code == 200
    assert dash_resp.json()["total_events"] >= 2
    assert dash_resp.json()["indexed_documents_count"] >= 5


def test_unavailable_ollama_graceful_fallback(test_env):
    """Verify that when Ollama is offline/unreachable, plan generation falls back gracefully."""
    client = test_env["client"]
    db = test_env["db"]
    seed_initial_data(db)

    # Point OllamaGenerationService at an unreachable local port
    offline_ollama = OllamaGenerationService(
        base_url="http://127.0.0.1:59999",
        model_name="nonexistent-model",
        timeout_seconds=0.5,
    )
    set_generation_service(offline_ollama)

    resp = client.post(
        "/api/events",
        json={
            "name": "Offline Fallback Test Event",
            "event_type": "community",
            "location": "Chennai",
            "total_budget": 50000,
            "guest_count": 100,
            "event_date": "2027-09-10",
            "generate_initial_plan": True,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["generation_mode"] == "deterministic_fallback"
    assert len(data["theme_recommendations"]) >= 1
    assert data["budget"]["total_budget"] == 50000
    assert len(data["citations"]) >= 1
