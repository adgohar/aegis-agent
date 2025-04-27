from typing import List, Dict
import pymc as pm

from backend.models.models import (
    Event,
    RiskScore,
    GeopoliticalRiskCategory
)


class BayesianRiskAssessmentService:
    """
    Service that computes Bayesian-based risk scores for geopolitical categories,
    given a collection of events with likelihood, impact, and risk_score assessments.
    """

    def __init__(self):
        pass

    @staticmethod
    def compute_geopolitical_risk_scores(
            supply_chain_id: str,
            events: List[Event],
            kappa: float = 5.0,
            default_no_data_score: float = 0.1
    ) -> RiskScore:
        """
        Computes posterior mean risk scores for each GeopoliticalRiskCategory
        using a Bayesian Beta model. Takes a list of events (historical + newly gathered),
        filters relevant data by subcategory, and returns a RiskScore model.

        A Beta(1,4) prior is used here, giving a mean of 0.2. Categories
        without any events are assigned a default score of 0.1 unless
        overridden.

        :param supply_chain_id: Identifier for the relevant supply chain.
        :param events: List of Event objects (historical + newly gathered).
        :param kappa: Concentration parameter for the Beta distribution.
        :param default_no_data_score: Default score for categories with no data.
        :return: A RiskScore object containing a score in [0,1] for each
                 geopolitical subcategory.
        """

        # Dictionary to hold severities for each geopolitical category.
        category_severities: Dict[GeopoliticalRiskCategory, List[float]] = {
            cat: [] for cat in GeopoliticalRiskCategory
        }

        # Gather severity values by category from relevant events.
        for e in events:
            if (
                    not e.risk_assessment or
                    not e.risk_assessment.is_relevant or
                    not e.risk_categories or
                    e.risk_assessment.likelihood is None or
                    e.risk_assessment.impact is None
            ):
                continue

            normalized_severity = e.risk_assessment.risk_score

            # Scan the event's risk_categories for "Geopolitical" and match subcategories.
            for rcat in e.risk_categories:
                if rcat.class_name.lower() == "geopolitical" and rcat.families:
                    for family in rcat.families:
                        for cat_enum in GeopoliticalRiskCategory:
                            if family.lower() == cat_enum.value.lower():
                                category_severities[cat_enum].append(normalized_severity)
                                break

        def _posterior_mean(severities: List[float]) -> float:
            """
            Computes the posterior mean for theta using a Bayesian Beta model:
            - Prior: Beta(1, 4) → mean of 0.2 (pessimistic prior)
            - Observations: Modeled as Beta(kappa * theta, kappa * (1 - theta))
            """
            with pm.Model() as model:
                # Define prior
                theta = pm.Beta("theta", alpha=1, beta=4)

                # Likelihood based on observed severity scores
                pm.Beta("s_obs", alpha=kappa * theta, beta=kappa * (1 - theta), observed=severities)

                # Sample from posterior
                trace = pm.sample(draws=1000, tune=500, chains=2, cores=1, progressbar=False)

            # Return posterior mean of theta
            return float(trace.posterior["theta"].mean().item())

        # Compute risk scores (posterior means) for each category.
        scores_dict: Dict[GeopoliticalRiskCategory, float] = {}
        for cat_enum, severities_list in category_severities.items():
            if not severities_list:
                scores_dict[cat_enum] = default_no_data_score
            else:
                scores_dict[cat_enum] = _posterior_mean(severities_list)

        # Construct and return the RiskScore model.
        return RiskScore(
            supply_chain_id=supply_chain_id,
            scores=scores_dict
        )
