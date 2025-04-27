from typing import List, Optional
from tinydb import TinyDB, Query
from pathlib import Path

from backend.models.models import RiskScore, Event


class DBService:
    def __init__(self, db_name="database.json"):
        self.db_path = Path(__file__).resolve().parent.parent / "data" / db_name
        self.db = TinyDB(self.db_path)
        self.supply_chain_table = self.db.table("supply_chains")
        self.event_table = self.db.table("events")
        self.risk_score_table = self.db.table("risk_scores")
        self.settings_table = self.db.table("settings")

    # Supply chain
    def add_supply_chain(self, supply_chain):
        self.supply_chain_table.upsert(supply_chain, Query().id == supply_chain["id"])

    def get_supply_chain(self, supply_chain_id):
        return self.supply_chain_table.get(Query().id == supply_chain_id)

    def get_all_supply_chains(self):
        return self.supply_chain_table.all()

    def save_selected_supply_chain(self, supply_chain_id):
        self.settings_table.upsert(
            {"key": "selected_supply_chain", "value": supply_chain_id},
            Query().key == "selected_supply_chain"
        )

    def get_selected_supply_chain(self) -> Optional[str]:
        setting = self.settings_table.get(Query().key == "selected_supply_chain")
        return setting["value"] if setting else None

    # Event Storage
    def save_events(self, events: List[Event]):
        for event in events:
            self.event_table.upsert(event.dict(), Query().id == event.id)

    def get_all_events(self) -> List[Event]:
        return [Event(**record) for record in self.event_table.all()]

    def get_event_by_id(self, event_id: str) -> Optional[Event]:
        record = self.event_table.get(Query().id == event_id)
        return Event(**record) if record else None

    def delete_all_events(self):
        self.event_table.truncate()

    def get_unassessed_events(self) -> List[Event]:
        return [
            Event(**record)
            for record in self.event_table.search(Query().risk_assessment == None)
        ]

    def get_assessed_events(self, supply_chain_id: str) -> List[Event]:
        """Retrieve only events that have been assessed for a given supply chain
        and are marked as relevant (i.e., risk_assessment.is_relevant is True)."""
        return [
            Event(**record)
            for record in self.event_table.search(
                (Query().supply_chain_id == supply_chain_id) &
                (Query().risk_assessment != None) &
                (Query().risk_assessment.is_relevant == True)
            )
        ]

    def save_event_assessment(self, event: Event):
        self.event_table.upsert(event.dict(), Query().id == event.id)

    def delete_event(self, event_id: str):
        self.event_table.remove(Query().id == event_id)

    def reset_all_event_assessments(self):
        self.event_table.update({"risk_assessment": None})

    # Risk Scores
    def add_or_update_risk_score(self, risk_score: RiskScore):
        self.risk_score_table.upsert(
            risk_score.dict(),
            Query().supply_chain_id == risk_score.supply_chain_id
        )

    def get_risk_score(self, supply_chain_id: str) -> Optional[RiskScore]:
        record = self.risk_score_table.get(Query().supply_chain_id == supply_chain_id)
        return RiskScore(**record) if record else None

    def get_all_risk_scores(self) -> List[RiskScore]:
        return [RiskScore(**record) for record in self.risk_score_table.all()]

    def delete_risk_score(self, supply_chain_id: str):
        self.risk_score_table.remove(Query().supply_chain_id == supply_chain_id)
