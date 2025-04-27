from typing import List
from backend.models.models import Event, SupplyChain, EventRiskAssessment
from backend.services.gpt_service import GPTService

LIKELIHOOD_MAPPING = {
    "Rare": 0.001,
    "Unlikely": 0.01,
    "Possible": 0.1,
    "Likely": 0.5,
    "Almost Certain": 0.9
}

IMPACT_MAPPING = {
    "Insignificant": 0.001,
    "Minor": 0.01,
    "Moderate": 0.1,
    "Major": 0.5,
    "Catastrophic": 0.9
}


class EventRelevanceAssessmentService:
    def __init__(self):
        self.gpt_service = GPTService()

    def assess_events(self, supply_chain: SupplyChain, events: List[Event]) -> List[Event]:
        """
        Assess relevance, likelihood, and impact for a list of events in a single GPT request per event.
        """
        for event in events:
            self._assess_event(supply_chain, event)

        return events

    def _assess_event(self, supply_chain: SupplyChain, event: Event) -> None:
        """
        Determines if an event is relevant. If relevant, it also assesses likelihood and impact.
        """

        prompt_messages = self._build_gpt_prompt(supply_chain, event)

        try:
            response = self.gpt_service.call_gpt_with_schema(
                model="gpt-4o-mini",
                messages=prompt_messages,
                schema=EventRiskAssessment
            )

            is_relevant = response.is_relevant
            reason = response.reason
            likelihood_value = response.likelihood
            impact_value = response.impact

            event.supply_chain_id = supply_chain.id

            if not is_relevant:
                event.risk_assessment = EventRiskAssessment(
                    is_relevant=False,
                    reason=reason
                )
            else:
                # Calculate the raw risk as the sum of likelihood and impact
                raw_risk = likelihood_value + impact_value
                # Normalize the risk:
                # Minimum possible raw risk = 0.001 + 0.001 = 0.002
                # Maximum possible raw risk = 0.9 + 0.9 = 1.8
                normalized_risk = (raw_risk - 0.002) / (1.8 - 0.002)

                event.risk_assessment = EventRiskAssessment(
                    is_relevant=True,
                    likelihood=likelihood_value,
                    impact=impact_value,
                    risk_score=normalized_risk,
                    reason=reason
                )

        except Exception as e:
            print(f"Error assessing event: {e}")
            event.risk_assessment = EventRiskAssessment(
                is_relevant=False,
                reason="Assessment failed due to an error."
            )

    @staticmethod
    def _build_gpt_prompt(supply_chain: SupplyChain, event: Event) -> List[dict]:
        system_prompt = (
            "You are an expert in supply chain risk management. Your task is to analyze an event and determine:\n"
            "1. **Whether it is relevant to the supply chain** (True/False).\n"
            "2. **If relevant, what is its likelihood and impact?**\n\n"
            "**Step 1: Assess Relevance**\n"
            "An event is **relevant** if it has a direct or indirect effect on the supply chain. Consider:\n"
            "- **Location:** Does the event affect supply chain nodes, suppliers, or transport routes?\n"
            "- **Risk Categories:** Are the risks associated with the event relevant to supply chain operations?\n"
            "- **Broader Impacts:** Could this event cause indirect disruptions (e.g., regulatory changes, market shifts)?\n"
            "If **not relevant**, return:\n"
            "{'is_relevant': false, 'likelihood': null, 'impact': null, 'reason': 'Explanation'}\n\n"
            "**Step 2: If Relevant, Assess Likelihood and Impact**\n"
            "**Likelihood (Probability of Disruption):**\n"
            "- Rare (0.001) – Extremely unlikely but possible.\n"
            "- Unlikely (0.01) – Has happened before but is improbable.\n"
            "- Possible (0.1) – Could reasonably occur under certain conditions.\n"
            "- Likely (0.5) – Expected to occur in many situations.\n"
            "- Almost Certain (0.9) – Nearly inevitable.\n\n"
            "**Impact (Severity of Disruption):**\n"
            "- Insignificant (0.001) – No/minimal effect.\n"
            "- Minor (0.01) – Small, manageable disruptions.\n"
            "- Moderate (0.1) – Noticeable disruptions requiring intervention.\n"
            "- Major (0.5) – Significant disruptions.\n"
            "- Catastrophic (0.9) – Severe disruptions threatening business continuity.\n\n"
            "**Final Output Format:**\n"
            "{'is_relevant': true/false, 'likelihood': 'Rare/Possible/etc.', 'impact': 'Minor/Moderate/etc.', 'reason': 'Explanation'}"
        )

        user_prompt = (
            f"Supply Chain:\n"
            f"Company: {supply_chain.companyName}\n"
            f"Description: {supply_chain.description}\n"
            f"Nodes:\n" +
            "\n".join(
                f"- {node.type} in {node.location.city or node.location.region or node.location.country}"
                for node in supply_chain.nodes
            ) +
            f"\n\nEvent:\n"
            f"Title: {event.title}\n"
            f"Description: {event.description}\n"
            f"Location: {event.location}\n"
            f"Risk Categories: {event.risk_categories}\n\n"
            "Task:\n"
            "1. Determine whether this event is **relevant**.\n"
            "2. If relevant, assign a **likelihood** and **impact** based on the provided categories.\n"
            "3. Provide a single **justification** that explains all three aspects."
        )

        return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
