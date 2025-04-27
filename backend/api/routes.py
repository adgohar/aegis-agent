import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Body

from backend.models.models import SupplyChain, Event, RiskScore
from backend.services.bayesian_risk_assessment_service import BayesianRiskAssessmentService
from backend.services.db_service import DBService
from backend.services.event_detection_service import EventDetectionService
from backend.services.event_relevance_assessment_service import EventRelevanceAssessmentService

router = APIRouter()

db_service = DBService()
event_service = EventDetectionService()
event_relevance_service = EventRelevanceAssessmentService()
bayesian_service = BayesianRiskAssessmentService()

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@router.on_event("startup")
def initialize_supply_chains():
    supply_chain_files = DATA_DIR.glob("SC_Example_*.json")
    for file_path in supply_chain_files:
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                supply_chain = {
                    "id": str(data["id"]),
                    "companyName": data.get("companyName", "Unknown Company"),
                    "description": data.get("description", "No description available."),
                    "nodes": data.get("nodes", []),
                    "edges": data.get("edges", [])
                }
                db_service.add_supply_chain(supply_chain)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading supply chain file {file_path}: {e}")


# Welcome endpoint
@router.get("/")
def read_root():
    return {"message": "Welcome to the Supply Chain Tool API"}


# ================================
# Supply Chain Endpoints
# ================================

@router.get("/supply_chains")
def get_supply_chains():
    """Fetch all supply chains from the database."""
    supply_chains = db_service.get_all_supply_chains()
    return {"supply_chains": supply_chains}


@router.post("/supply_chains/selected")
def set_selected_supply_chain(body: dict = Body(...)):
    """Set the currently selected supply chain."""
    supply_chain_id = body.get("supply_chain_id")
    if not supply_chain_id:
        raise HTTPException(status_code=400, detail="supply_chain_id is required.")
    supply_chain = db_service.get_supply_chain(supply_chain_id)
    if not supply_chain:
        raise HTTPException(status_code=404, detail=f"Supply chain {supply_chain_id} not found.")
    db_service.save_selected_supply_chain(supply_chain_id)
    return {"message": f"Supply chain {supply_chain_id} set as selected."}


@router.get("/supply_chains/selected")
def get_selected_supply_chain():
    """Fetch the currently selected supply chain."""
    supply_chain_id = db_service.get_selected_supply_chain()
    if not supply_chain_id:
        raise HTTPException(status_code=404, detail="No supply chain selected.")
    return db_service.get_supply_chain(supply_chain_id)


@router.get("/supply_chains/{id}")
def get_supply_chain(id: int):
    """Fetch predefined supply chain data based on the provided ID."""
    file_name = f"SC_Example_0{id}.json"
    try:
        with open(DATA_DIR / file_name, "r") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        return {"error": f"Supply chain file not found: {file_name}."}
    except json.JSONDecodeError:
        return {"error": "Error decoding supply chain JSON file."}


# ================================
# Event Endpoints
# ================================

@router.get("/events/new")
def fetch_new_events(
        query: str = "supply chain disruptions OR supply chain risks OR geopolitical challenges",
        from_date: str = None,
        to_date: str = None,
        page_size: int = 10
):
    """
    Fetch and process fresh news articles into events.
    Accepts a query, optional date range, and page size.
    """
    try:
        events = event_service.process_events(query, page_size, from_date, to_date)
        return {"events": [event.dict() for event in events]}
    except Exception as e:
        return {"error": f"Failed to fetch and process events: {str(e)}"}


@router.get("/events/saved")
def get_saved_events():
    """Retrieve all saved events from the database."""
    try:
        events = db_service.get_all_events()
        return {"events": [event.dict() for event in events]}
    except Exception as e:
        return {"error": f"Failed to retrieve saved events: {str(e)}"}


@router.post("/supply_chains/{id}/events/assess")
def assess_unassessed_events(id: int):
    """Assess unassessed events for a given supply chain."""
    try:
        file_name = f"SC_Example_0{id}.json"
        with open(DATA_DIR / file_name, "r") as f:
            supply_chain_data = json.load(f)
        supply_chain = SupplyChain(**supply_chain_data)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Supply chain file not found: {file_name}.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading supply chain: {e}")

    try:
        events = db_service.get_unassessed_events()
        if not events:
            return {"message": "No unassessed events found."}

        assessed_events = event_relevance_service.assess_events(supply_chain, events)

        for event in assessed_events:
            db_service.save_event_assessment(event)

        return {"assessed_events": [event.dict() for event in assessed_events]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assess event risk: {str(e)}")


@router.get("/supply_chains/{id}/events/assessed")
def get_assessed_events(id: int):
    """
    Retrieve events that have already been assessed for the given supply chain.
    """
    try:
        assessed_events = db_service.get_assessed_events(str(id))
        return {"assessed_events": [event.dict() for event in assessed_events]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve assessed events: {str(e)}")


@router.put("/events/update")
async def update_event(event_data: Event):
    """
    Updates an existing event using data from the request body.
    The event data must include the id (which may be a URL).
    """
    event_id = event_data.id
    if not event_id:
        raise HTTPException(status_code=400, detail="Event ID is required")
    existing_event = db_service.get_event_by_id(event_id)
    if not existing_event:
        raise HTTPException(status_code=404, detail="Event not found")
    try:
        db_service.save_event_assessment(event_data)
        return {"message": "Event updated successfully", "event": event_data.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update event: {str(e)}")


@router.delete("/events/delete")
async def delete_event(event_data: Event):
    """
    Deletes an event using data from the request body.
    The event data must include the id (which may be a URL).
    """
    event_id = event_data.id
    if not event_id:
        raise HTTPException(status_code=400, detail="Event ID is required")
    existing_event = db_service.get_event_by_id(event_id)
    if not existing_event:
        raise HTTPException(status_code=404, detail="Event not found")
    try:
        db_service.delete_event(event_id)
        return {"message": "Event deleted successfully", "event_id": event_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete event: {str(e)}")


@router.post("/events/reset-assessments")
def reset_event_assessments():
    """
    Reset the risk assessments for all events in the database.
    """
    try:
        db_service.reset_all_event_assessments()
        return {"message": "Risk assessments have been reset for all events."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset event risk assessments: {e}")


# ================================
# Bayesian Risk Endpoints
# ================================

@router.get("/supply_chains/selected/risk_scores")
def compute_bayesian_risk_scores():
    """
    Computes Bayesian risk scores for the currently selected supply chain
    using assessed events and saves the result in the database.
    """
    supply_chain_id = db_service.get_selected_supply_chain()
    if not supply_chain_id:
        raise HTTPException(status_code=404, detail="No supply chain selected.")
    events = db_service.get_assessed_events(supply_chain_id)
    if not events:
        return {"message": f"No assessed events found for supply chain {supply_chain_id}."}
    risk_score: RiskScore = bayesian_service.compute_geopolitical_risk_scores(
        supply_chain_id=str(supply_chain_id),
        events=events,
        kappa=5.0,
        default_no_data_score=0.1
    )
    db_service.add_or_update_risk_score(risk_score)
    return {
        "supply_chain_id": risk_score.supply_chain_id,
        "risk_scores": {category.value: score for category, score in risk_score.scores.items()}
    }


@router.get("/supply_chains/selected/risk_scores/stored")
def get_stored_bayesian_risk_scores():
    """
    Retrieves the stored Bayesian risk scores for the currently selected supply chain.
    """
    supply_chain_id = db_service.get_selected_supply_chain()
    if not supply_chain_id:
        raise HTTPException(status_code=404, detail="No supply chain selected.")
    stored_score = db_service.get_risk_score(str(supply_chain_id))
    if not stored_score:
        return {"message": f"No stored risk scores found for supply chain {supply_chain_id}."}
    return {
        "supply_chain_id": stored_score.supply_chain_id,
        "risk_scores": {category: score for category, score in stored_score.scores.items()}
    }
