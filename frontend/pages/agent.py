# frontend/pages/event_agent.py

import os, sys

# 1) Add frontend/ to module search path so we can import utils/
THIS_DIR = os.path.dirname(__file__)                              # .../frontend/pages
FRONTEND_ROOT = os.path.abspath(os.path.join(THIS_DIR, ".."))     # .../frontend
sys.path.insert(0, FRONTEND_ROOT)

import re
from datetime import date, timedelta

import streamlit as st
from pages.events_news import fetch_and_store_events
from utils.tools import assess_and_store_events, load_assessed_events_to_map

import smolagents
from smolagents import CodeAgent, tool
from smolagents.models import HfApiModel

import ast

# ─── 1. Load system prompt from prompts.yaml ────────────────────────────────────

PROMPT_PATH = os.path.join(os.path.dirname(__file__), "prompts.yaml")
with open(PROMPT_PATH, "r") as f:
    system_prompt = f.read().strip()

# ─── 2. Define the single agent tool ─────────────────────────────────────────────

os.environ["HF_TOKEN"]="hf_XXXXXXXXXXXXXXXXXXXX"

# ─── 3. Instantiate the agent ───────────────────────────────────────────────────

# Initialize your LLM model (Hugging Face endpoint, etc.)
model = HfApiModel(
    max_tokens=2096,
    temperature=0.5,
    model_id="Qwen/Qwen2.5-Coder-32B-Instruct",
    custom_role_conversions=None,
)


# Build the agent with our single tool
agent = CodeAgent(
    model=model,
    tools=[fetch_and_store_events, assess_and_store_events, load_assessed_events_to_map]
)

# ─── 4. Streamlit UI integration ────────────────────────────────────────────────

st.header("Agent Automator")
user_prompt = st.text_input(
    "Agent Prompt",
    value="Fetch 15 articles about Supply Chain Disruptions in the last 14 days"
)

if st.button("Run Agent"):
    full_prompt = f"{system_prompt}\nTask: \"{user_prompt}\""
    raw = agent(full_prompt)

    # Try to parse the raw output into a dict
    try:
        result = ast.literal_eval(raw)
    except Exception:
        result = raw

    # If it’s a dict, display its fields
    if isinstance(result, dict):
        st.markdown("### Task Outcome")
        st.write(f"**Short:** {result.get('task_outcome_short')}")
        st.write(f"**Details:** {result.get('task_outcome_detailed')}")
        st.write(f"**Context:** {result.get('additional_context')}")
    else:
        # Fallback: just show the raw response
        st.write(result)


# Now, your existing code (in event_news.py) can remain below,
# reading from st.session_state.events for display.
if 'events' in st.session_state and st.session_state.events:
    for ev in st.session_state.events.get(st.session_state.last_topic, []):
        st.write(f"- [{ev['title']}]({ev['url']})")
else:
    st.info("No events fetched yet. Use the Agent sidebar.")
