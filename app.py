"""TofuTemple signup page. Run with: uv run streamlit run app.py"""

import hmac
import logging
from pathlib import Path

import requests
import streamlit as st

from tofu_signup.config import load_config
from tofu_signup.limits import Limits
from tofu_signup.soap import Outcome, classify, execute
from tofu_signup.validation import ACCOUNT_RULE, PASSWORD_RULE, validate_account, validate_password

REALMLIST = "set realmlist tofutemple.zapto.org"


@st.cache_resource
def get_config():
    return load_config()


@st.cache_resource
def get_limits(invite_max_fails: int, creates_per_hour: int) -> Limits:
    return Limits(invite_max_fails, creates_per_hour)


@st.cache_resource
def get_logger() -> logging.Logger:
    Path("logs").mkdir(exist_ok=True)
    logger = logging.getLogger("tofu_signup")
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler("logs/signup.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    return logger


cfg = get_config()
limits = get_limits(cfg.invite_max_fails, cfg.creates_per_hour)
log = get_logger()

st.set_page_config(page_title="TofuTemple signup", page_icon="🍥")
st.image(str(Path(__file__).parent / "assets" / "tofu.png"), width=120)
st.title("TofuTemple account signup")

if cfg.debug:
    st.warning("Debug mode is on: raw SOAP responses are shown. Turn it off before sharing the page.")

# Gate: invite code.
if not st.session_state.get("invited"):
    if limits.invite_locked():
        st.error("Too many wrong invite codes. Ask Chris.")
        st.stop()
    with st.form("invite"):
        code = st.text_input("Invite code", type="password")
        if st.form_submit_button("Continue"):
            if hmac.compare_digest(code.encode(), cfg.invite_code.encode()):
                st.session_state["invited"] = True
                st.rerun()
            limits.record_invite_fail()
            log.info("invite rejected")
            st.error("That invite code is not valid.")
    st.stop()

# Signup form.
with st.form("signup"):
    name_in = st.text_input("Account name", help=ACCOUNT_RULE)
    pass_in = st.text_input("Password", type="password", help=PASSWORD_RULE)
    submitted = st.form_submit_button("Create account")

if submitted:
    name = validate_account(name_in)
    if name is None or not validate_password(pass_in):
        log.info("invalid input")
        st.error(f"Invalid input. Account name: {ACCOUNT_RULE} Password: {PASSWORD_RULE}")
        st.stop()
    if not limits.try_reserve_create():
        log.info("rate limited name=%s", name)
        st.error("Too many accounts created in the last hour. Try again later.")
        st.stop()

    try:
        resp = execute(cfg.soap_url, cfg.soap_user, cfg.soap_pass, f"account create {name} {pass_in}")
    except requests.RequestException as e:
        log.warning("soap unreachable name=%s err=%s", name, type(e).__name__)
        st.error("The game server is not reachable right now. Ask Chris.")
        st.stop()

    outcome = classify(resp)
    log.info("name=%s outcome=%s status=%s text=%r", name, outcome.value, resp.status, resp.text)

    if outcome is Outcome.CREATED:
        st.success(f"Account {name} created. In your WoW folder, set Data/enUS/realmlist.wtf to:")
        st.code(REALMLIST, language=None)
    elif outcome is Outcome.TAKEN:
        st.error("That account name is already taken.")
    elif outcome is Outcome.AUTH_FAIL:
        st.error("The signup service is misconfigured. Ask Chris.")
    else:
        st.error("Something went wrong. Ask Chris.")

    if cfg.debug:
        st.code(f"HTTP {resp.status} fault={resp.is_fault}\n{resp.text}\n\n{resp.raw}", language=None)
