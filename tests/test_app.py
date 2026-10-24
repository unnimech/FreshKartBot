import csv, importlib, os, sys
from pathlib import Path
import pytest
from dotenv import load_dotenv
from langchain_core.runnables import RunnableLambda
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")
HAS_KEY = bool(os.getenv("OPENROUTER_API_KEY"))
TICKETS = list(csv.DictReader(open(ROOT / "data" / "tickets.csv", encoding="utf-8")))
BY_MSG = {t["message"]: t["expected_intent"] for t in TICKETS}

def fake_llm(prompt_value):
    """Stands in for the LLM: intent prompt -> expected intent, lane prompts -> a canned reply."""
    msgs = prompt_value.to_messages()
    if "Classify" in msgs[0].content:
        return BY_MSG.get(msgs[-1].content, "general") + ",neutral"
    return "Fake reply."

def load_bot(monkeypatch, fake):
    import langchain_openai
    if fake:
        monkeypatch.setattr(langchain_openai, "ChatOpenAI", lambda **kw: RunnableLambda(fake_llm))
        monkeypatch.setenv("OPENROUTER_API_KEY", os.getenv("OPENROUTER_API_KEY", "test-key"))
    sys.modules.pop("bot", None)
    return importlib.import_module("bot")

@pytest.fixture
def fake_bot(monkeypatch):
    yield load_bot(monkeypatch, fake=True)
    sys.modules.pop("bot", None)

@pytest.fixture
def real_bot(monkeypatch):
    yield load_bot(monkeypatch, fake=False)
    sys.modules.pop("bot", None)

def app():
    return AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()

# ---- offline: rules and router ----
CLEAN = {"customer_id": "C01", "fraud_score": "0.05", "refunds_30d": "0"}
BASE = {"intent": "missing_item",
        "order": {"amount": "210", "status": "delivered", "delivered_at": "2026-10-12 18:40", "substituted": "n"},
        "customer": CLEAN, "inventory": {"expired_confirmed": False, "baby": False},
        "rider": {"gps_delivered": "y"}, "safety": False, "claimed_amount": None}

@pytest.mark.parametrize("change,route", [
    ({}, "auto_refund"),
    ({"claimed_amount": 2000.0}, "human_review"),
    ({"inventory": {"expired_confirmed": False, "baby": True}}, "human_review"),
    ({"safety": True}, "human_review"),
    ({"intent": "general"}, "info"),
    ({"order": None}, "info"),
    ({"intent": "mystery"}, "human_review"),
])
def test_decide_route(fake_bot, change, route):
    assert fake_bot.decide_route({"signals": {**BASE, **change}})["route"] == route

def test_router_all_18_tickets(fake_bot):
    results = fake_bot.router.batch([{"input": t["message"], "chat_history": []} for t in TICKETS])
    wrong = [t["id"] for t, r in zip(TICKETS, results) if r["route"] != t["expected_route"]]
    assert len(TICKETS) == 18 and not wrong, wrong

def test_memory_recovers_order_id(fake_bot):
    from langchain_core.messages import HumanMessage
    x = {"input": "refund kab milega?", "chat_history": [HumanMessage(content="FK1016 ka status?")]}
    assert fake_bot.order_id_from(x) == "FK1016"

# ---- UI with a fake LLM ----
def test_app_loads(fake_bot):
    at = app()
    assert not at.exception
    assert at.title[0].value == "FreshKart Support Desk"
    assert len(at.tabs) == 4 and len(at.dataframe) == 4  # Data tab: 4 CSVs

def test_chat_roundtrip(fake_bot):
    at = app()
    at.chat_input[0].set_value(TICKETS[0]["message"]).run()
    assert not at.exception
    assert [m.name for m in at.chat_message] == ["user", "assistant"]
    assert at.expander[0].label == "Why this answer?"
    assert "auto_refund" in at.expander[0].markdown[0].value
    assert "Fake reply." in at.chat_message[1].markdown[0].value
    assert at.session_state["messages"][1]["route"] == "auto_refund"

def test_ops_queue_and_new_chat(fake_bot):
    at = app()
    at.chat_input[0].set_value(TICKETS[8]["message"]).run()  # T09 food safety
    assert at.session_state["log"][0]["route"] == "human_review"
    assert any(m.label == "human_review" and m.value == "1" for m in at.metric)
    assert len(at.dataframe) == 5  # queue + 4 data tables
    next(b for b in at.sidebar.button if b.label == "New chat").click().run()
    assert at.session_state["messages"] == [] and len(at.chat_message) == 0

def test_sample_ticket_send(fake_bot):
    at = app()
    next(b for b in at.sidebar.button if b.label == "Send").click().run()
    assert len(at.chat_message) == 2

def test_missing_key_shows_error(monkeypatch, fake_bot):
    monkeypatch.delenv("OPENROUTER_API_KEY")
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: None)
    at = app()
    assert at.error and "OPENROUTER_API_KEY" in at.error[0].value

# ---- live (real OpenRouter calls) ----
@pytest.mark.skipif(not HAS_KEY, reason="no OPENROUTER_API_KEY")
@pytest.mark.parametrize("tid,route", [("T09", "human_review"), ("T01", "auto_refund")])
def test_live_round_trip(real_bot, tid, route):
    msg = next(t["message"] for t in TICKETS if t["id"] == tid)
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=90).run()
    at.chat_input[0].set_value(msg).run()
    assert not at.exception
    last = at.session_state["messages"][-1]
    assert last["route"] == route and last["content"].strip()
