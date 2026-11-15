"""Minimal client for the AzerothCore worldserver SOAP interface (see azerothcore.org/wiki/remote-access)."""

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from enum import Enum
from xml.sax.saxutils import escape

import requests

ENVELOPE = (
    '<SOAP-ENV:Envelope'
    ' xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"'
    ' xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/"'
    ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
    ' xmlns:xsd="http://www.w3.org/2001/XMLSchema"'
    ' xmlns:ns1="urn:AC">'
    '<SOAP-ENV:Body><ns1:executeCommand><command>{command}</command></ns1:executeCommand></SOAP-ENV:Body>'
    '</SOAP-ENV:Envelope>'
)

# Substrings of the console text, to be filled from live captures. Keep every response string here.
# UNVERIFIED: empty until captured from the live server.
KNOWN_RESPONSES = {
    "taken": [],
}


class Outcome(Enum):
    CREATED = "created"
    TAKEN = "taken"
    AUTH_FAIL = "auth_fail"
    UNREACHABLE = "unreachable"
    UNKNOWN = "unknown"


@dataclass
class SoapResponse:
    status: int | None
    is_fault: bool
    text: str
    raw: str


def build_envelope(command: str) -> str:
    return ENVELOPE.format(command=escape(command))


def execute(url: str, user: str, password: str, command: str, timeout: float = 5.0) -> SoapResponse:
    """POST one console command. Raises requests.RequestException if the server is unreachable."""
    resp = requests.post(
        url,
        data=build_envelope(command).encode("utf-8"),
        auth=(user, password),
        headers={"Content-Type": "application/xml"},
        timeout=timeout,
    )
    return parse(resp.status_code, resp.text)


def parse(status: int | None, body: str) -> SoapResponse:
    """Pull the <result> or <faultstring> text out of a SOAP body, matching on local tag names."""
    text, is_fault = "", False
    try:
        for el in ET.fromstring(body).iter():
            tag = el.tag.rsplit("}", 1)[-1]
            if tag == "result":
                text = el.text or ""
            elif tag == "faultstring":
                text, is_fault = el.text or "", True
    except ET.ParseError:
        text, is_fault = body, True
    return SoapResponse(status=status, is_fault=is_fault, text=text.replace("\r", "").strip(), raw=body)


def classify(resp: SoapResponse) -> Outcome:
    # UNVERIFIED: assumes the core returns <result> when a command succeeds and a Fault when it returns false.
    if resp.status == 401 or "401" in resp.text:
        return Outcome.AUTH_FAIL
    lowered = resp.text.lower()
    if any(s.lower() in lowered for s in KNOWN_RESPONSES["taken"]):
        return Outcome.TAKEN
    if not resp.is_fault:
        return Outcome.CREATED
    return Outcome.UNKNOWN
