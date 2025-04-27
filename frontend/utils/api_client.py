import requests

BASE_URL = "http://backend:8000"


def get_root_message():
    response = requests.get(f"{BASE_URL}/")
    response.raise_for_status()
    return response.json()


def fetch_new_events(query: str, page_size: int = 10, from_date: str = None, to_date: str = None):
    """
    Fetches new events using the /events/new endpoint.
    """
    params = {"query": query, "page_size": page_size}
    if from_date:
        params["from_date"] = from_date
    if to_date:
        params["to_date"] = to_date
    response = requests.get(f"{BASE_URL}/events/new", params=params)
    response.raise_for_status()
    return response.json()


def fetch_saved_events():
    """
    Fetches saved events from the /events/saved endpoint.
    """
    response = requests.get(f"{BASE_URL}/events/saved")
    response.raise_for_status()
    return response.json()


def assess_unassessed_events(supply_chain_id: int = 1):
    """
    Assesses unassessed events for the given supply chain via the /supply_chains/{id}/events/assess endpoint.
    """
    response = requests.post(f"{BASE_URL}/supply_chains/{supply_chain_id}/events/assess", json={})
    response.raise_for_status()
    data = response.json()
    return data.get("assessed_events", [])


def fetch_assessed_events(supply_chain_id: int = 1):
    """
    Fetches assessed events for the given supply chain via the /supply_chains/{id}/events/assessed endpoint.
    """
    response = requests.get(f"{BASE_URL}/supply_chains/{supply_chain_id}/events/assessed")
    response.raise_for_status()
    return response.json()["assessed_events"]


def fetch_supply_chain(supply_chain_id: int):
    """
    Fetches the supply chain data for the specified ID.
    """
    response = requests.get(f"{BASE_URL}/supply_chains/{supply_chain_id}")
    response.raise_for_status()
    return response.json()


def fetch_supply_chains():
    """
    Fetches all supply chains from the backend.
    """
    response = requests.get(f"{BASE_URL}/supply_chains")
    response.raise_for_status()
    return response.json()["supply_chains"]


def set_selected_supply_chain(supply_chain_id: str):
    """
    Sets the selected supply chain via the /supply_chains/selected endpoint.
    """
    response = requests.post(f"{BASE_URL}/supply_chains/selected", json={"supply_chain_id": supply_chain_id})
    response.raise_for_status()
    return response.json()


def get_selected_supply_chain():
    """
    Fetches the currently selected supply chain from the /supply_chains/selected endpoint.
    """
    response = requests.get(f"{BASE_URL}/supply_chains/selected")
    response.raise_for_status()
    return response.json()


def fetch_bayesian_risk_scores():
    """
    Computes and fetches the latest Bayesian risk scores for the currently selected supply chain.
    """
    response = requests.get(f"{BASE_URL}/supply_chains/selected/risk_scores")
    response.raise_for_status()
    return response.json()


def fetch_stored_bayesian_risk_scores():
    """
    Fetches the stored Bayesian risk scores for the currently selected supply chain.
    """
    response = requests.get(f"{BASE_URL}/supply_chains/selected/risk_scores/stored")
    response.raise_for_status()
    return response.json()


def update_event(event: dict):
    """
    Updates an event via the /events/update endpoint.
    The event data (including its id, which may be a URL) is sent in the request body.
    """
    if "id" not in event:
        raise ValueError("Event must have an 'id' field.")
    response = requests.put(f"{BASE_URL}/events/update", json=event)
    response.raise_for_status()
    return response.json()


def delete_event(event: dict):
    """
    Deletes an event via the /events/delete endpoint.
    The event data (including its id, which may be a URL) is sent in the request body.
    """
    if "id" not in event:
        raise ValueError("Event must have an 'id' field.")
    response = requests.delete(f"{BASE_URL}/events/delete", json=event)
    response.raise_for_status()
    return response.json()
