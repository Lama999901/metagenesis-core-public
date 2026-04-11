#!/usr/bin/env python3
"""
MetaGenesis Core -- Multilingual Client Onboarding CLI

Any person on Earth runs this, communicates in their native language via
Claude AI, gets a verified bundle, and sees the $299 payment link.

Usage:
    python scripts/mg_onboard.py --api-key YOUR_CLAUDE_KEY
    ANTHROPIC_API_KEY=sk-... python scripts/mg_onboard.py

3-step flow:
  1. Client describes their work -> language detected, domain mapped
  2. Verification runs -> bundle created, 5 layers verified
  3. Result explained in client language -> payment link shown if PASS

Requires: anthropic Python package (pip install anthropic)
PPA: USPTO #63/996,819
"""

import argparse
import hashlib
import io
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

# Fix Windows cp1252 encoding
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# ---- Terminal colors --------------------------------------------------------

G = "\033[92m"
R = "\033[91m"
Y = "\033[93m"
C = "\033[96m"
B = "\033[1m"
DIM = "\033[2m"
X = "\033[0m"

# ---- Constants --------------------------------------------------------------

STRIPE_LINK = "https://buy.stripe.com/14AcN57qH19R1qN3QQ6Na00"
PILOT_URL = "https://metagenesis-core.dev/#pilot"
CONTACT_EMAIL = "yehor@metagenesis-core.dev"

DOMAIN_KEYWORDS = {
    "ml": {
        "keywords": [
            "machine learning", "ml", "deep learning", "neural network",
            "accuracy", "benchmark", "classification", "prediction",
            "model", "training", "inference", "ai", "artificial intelligence",
            "stock", "price prediction", "nlp", "computer vision",
            "transformer", "llm", "large language model",
        ],
        "claim": "ML_BENCH-01",
        "mg_domain": "ml",
    },
    "pharma": {
        "keywords": [
            "pharma", "drug", "admet", "molecule", "compound",
            "fda", "clinical", "solubility", "toxicity", "bioavailability",
            "medicament", "pharmaceutical", "medication", "medicine",
            "pharmacokinetics", "pharmacodynamics",
            "medicamentos", "medicamento", "farmac",
            "\u85ac", "\u533b\u85ac\u54c1",  # Japanese: drug, medicine
            "\u836f\u7269", "\u836f\u54c1",  # Chinese: drug, medicine
        ],
        "claim": "PHARMA-01",
        "mg_domain": "pharma",
    },
    "finance": {
        "keywords": [
            "finance", "var", "value at risk", "risk", "trading",
            "portfolio", "basel", "regulatory", "bank", "quant",
            "hedge fund", "derivatives", "options", "credit risk",
            "market risk", "monte carlo",
        ],
        "claim": "FINRISK-01",
        "mg_domain": "finance",
    },
    "materials": {
        "keywords": [
            "material", "young's modulus", "elastic", "elasticity",
            "steel", "aluminum", "titanium", "copper", "conductivity",
            "thermal", "calibration", "tensile", "stress", "strain",
            "modulus", "alloy", "metal",
            "\u5f3e\u6027\u7387", "\u6750\u6599",  # Japanese/Chinese: elasticity, material
            "\u6e2c\u5b9a", "\u6d4b\u91cf",        # Japanese: measurement, Chinese: measurement
            "\u92fc", "\u9285", "\u30a2\u30eb\u30df",  # Japanese: steel, copper, aluminum
        ],
        "claim": "MTR-1",
        "mg_domain": "materials",
    },
    "digital_twin": {
        "keywords": [
            "digital twin", "fem", "finite element", "simulation",
            "cfd", "displacement", "mesh", "fea", "ansys", "abaqus",
            "comsol", "structural analysis", "vibration", "modal",
            "\u6709\u9650\u5143", "\u4eff\u771f", "\u6a21\u62df",  # Chinese: finite element, simulation
            "\u6709\u9650\u8981\u7d20", "\u30b7\u30df\u30e5\u30ec\u30fc\u30b7\u30e7\u30f3",  # Japanese: FEM, simulation
        ],
        "claim": "DT-FEM-01",
        "mg_domain": "digital_twin",
    },
    "physics": {
        "keywords": [
            "physics", "boltzmann", "avogadro", "constant",
            "thermodynamics", "statistical mechanics", "entropy",
            "temperature", "si unit", "fundamental constant",
        ],
        "claim": "PHYS-01",
        "mg_domain": "physics",
    },
    "systems": {
        "keywords": [
            "system identification", "arx", "control", "pid",
            "transfer function", "state space", "feedback",
            "automation", "signal processing", "sensor",
        ],
        "claim": "SYSID-01",
        "mg_domain": "systems",
    },
    "agent": {
        "keywords": [
            "agent", "drift", "monitoring", "devops", "pipeline",
            "ci/cd", "data pipeline", "etl", "data quality",
        ],
        "claim": "AGENT-DRIFT-01",
        "mg_domain": "agent",
    },
}

SYSTEM_PROMPT = """\
You are a MetaGenesis Core verification expert. MetaGenesis Core is a \
cryptographic notary for computations — it certifies that a computer produced \
exactly this result, at exactly this time, in exactly this way.

CRITICAL: Detect the user's language from their FIRST message and respond \
in that SAME language for ALL subsequent messages. Never switch to English \
unless the user writes in English.

You know:
- 20 verification claims across 8 domains (ML, pharma, finance, materials, \
  digital twin, physics, systems, agent)
- 5 verification layers: SHA-256 integrity, semantic, step chain, bundle \
  signing (HMAC-SHA256), temporal commitment
- Price: $299 per verification bundle
- Physical anchor principle: where physical constants exist (kB, NA, E), \
  the verification chain is grounded in measured reality
- Patent: USPTO #63/996,819

Your job:
1. Understand what the user computes
2. Map their work to the correct domain and claim
3. Explain the verification result clearly
4. If PASS: show the $299 Stripe link and explain the value
5. If FAIL: explain why and how to fix

Be helpful, concise, and enthusiastic about verification.

Domain mapping:
- ML/AI/benchmarks/predictions -> ML_BENCH-01 (ml)
- Pharma/drugs/ADMET -> PHARMA-01 (pharma)
- Finance/VaR/risk -> FINRISK-01 (finance)
- Materials/modulus/calibration -> MTR-1 (materials)
- Digital twin/FEM/simulation -> DT-FEM-01 (digital_twin)
- Physics/constants/thermodynamics -> PHYS-01 (physics)
- System ID/control/ARX -> SYSID-01 (systems)
- Agent/drift/pipelines -> AGENT-DRIFT-01 (agent)
"""


def detect_domain_local(text: str) -> tuple:
    """Detect domain from text using keyword matching. Returns (domain_key, claim_id)."""
    text_lower = text.lower()
    best_domain = None
    best_score = 0

    for domain_key, config in DOMAIN_KEYWORDS.items():
        score = 0
        for kw in config["keywords"]:
            if kw in text_lower:
                score += len(kw)  # longer matches score higher
        if score > best_score:
            best_score = score
            best_domain = domain_key

    if best_domain is None:
        best_domain = "ml"  # default fallback

    cfg = DOMAIN_KEYWORDS[best_domain]
    return cfg["mg_domain"], cfg["claim"]


def _call_claude(client, messages: list, user_msg: str) -> str:
    """Send a message to Claude and get response."""
    messages.append({"role": "user", "content": user_msg})

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=messages,
    )

    assistant_text = response.content[0].text
    messages.append({"role": "assistant", "content": assistant_text})
    return assistant_text


def _log_session(domain: str, claim: str, language: str, passed: bool,
                 user_description: str, session_hash: str):
    """Log onboarding session to reports/onboarding_log.json."""
    log_path = REPO_ROOT / "reports" / "onboarding_log.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    entries = []
    if log_path.exists():
        try:
            entries = json.loads(log_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            entries = []

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_hash": session_hash,
        "domain": domain,
        "claim": claim,
        "language": language,
        "verification_passed": passed,
        "description_length": len(user_description),
    }
    entries.append(entry)

    log_path.write_text(
        json.dumps(entries, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return entry


def _detect_language(text: str) -> str:
    """Simple language detection from character ranges and common words."""
    has_hiragana = False
    has_katakana = False
    has_cjk = False
    has_hangul = False
    has_cyrillic = False

    for ch in text:
        cp = ord(ch)
        if 0x3040 <= cp <= 0x309F:
            has_hiragana = True
        elif 0x30A0 <= cp <= 0x30FF:
            has_katakana = True
        elif 0x4E00 <= cp <= 0x9FFF:
            has_cjk = True
        elif 0xAC00 <= cp <= 0xD7AF:
            has_hangul = True
        elif 0x0400 <= cp <= 0x04FF:
            has_cyrillic = True

    # Japanese: hiragana or katakana present (even with kanji)
    if has_hiragana or has_katakana:
        return "ja"
    if has_hangul:
        return "ko"
    if has_cjk:
        return "zh"
    if has_cyrillic:
        return "ru"

    # Check for common Spanish/Portuguese/French markers
    lower = text.lower()
    if any(w in lower for w in ["trabajo", "estoy", "necesito", "hago", "modelo"]):
        return "es"
    if any(w in lower for w in ["je travaille", "j'utilise", "nous"]):
        return "fr"
    if any(w in lower for w in ["ich arbeite", "wir", "berechnung"]):
        return "de"
    return "en"


def run_onboarding(api_key: str, mock_mode: bool = False,
                   mock_input: str = None, mock_responses: list = None):
    """Run the full 3-step onboarding flow.

    Args:
        api_key: Anthropic API key
        mock_mode: If True, use mock_input and mock_responses instead of real API
        mock_input: Pre-set user input for testing
        mock_responses: List of pre-set Claude responses for testing

    Returns:
        dict with session results (domain, claim, passed, language, session_hash)
    """
    from scripts.mg_client import run_claim, create_bundle, verify_bundle

    # Generate anonymous session hash
    session_id = os.urandom(16).hex()
    session_hash = hashlib.sha256(session_id.encode()).hexdigest()[:16]

    print()
    print(f"{B}{C}  MetaGenesis Core -- Client Onboarding{X}")
    print(f"{DIM}  Tamper-evident computation certification{X}")
    print(f"{DIM}  PPA: USPTO #63/996,819{X}")
    print()

    # Initialize Claude client or mock
    client = None
    messages = []
    mock_idx = [0]  # mutable for closure

    if not mock_mode:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            print(f"{R}ERROR:{X} anthropic package not installed.")
            print(f"  Run: pip install anthropic")
            return None
    else:
        def _mock_call(_client, _messages, _user_msg):
            if mock_responses and mock_idx[0] < len(mock_responses):
                resp = mock_responses[mock_idx[0]]
                mock_idx[0] += 1
                _messages.append({"role": "user", "content": _user_msg})
                _messages.append({"role": "assistant", "content": resp})
                return resp
            return "Mock response."

    # ---- Step 1: Ask what they compute ----
    print(f"  {C}[Step 1/3]{X} What do you compute?")
    print(f"  {DIM}Describe your work in any language.{X}")
    print()

    if mock_input:
        user_description = mock_input
        print(f"  > {user_description}")
    else:
        try:
            user_description = input(f"  > ").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n  {Y}Session cancelled.{X}")
            return None

    if not user_description:
        print(f"  {R}No input provided.{X}")
        return None

    # Detect language and domain
    language = _detect_language(user_description)
    domain, claim = detect_domain_local(user_description)

    print()
    print(f"  {G}Language detected:{X} {language}")
    print(f"  {G}Domain detected:{X}  {domain} ({claim})")
    print()

    # Get Claude's response about domain detection
    domain_prompt = (
        f"The user said: \"{user_description}\"\n\n"
        f"I detected their domain as {domain} (claim {claim}). "
        f"Greet them in their language, confirm you understand their domain, "
        f"and explain briefly what MetaGenesis verification will do for them. "
        f"Keep it under 150 words."
    )

    if mock_mode:
        response1 = _mock_call(client, messages, domain_prompt)
    else:
        response1 = _call_claude(client, messages, domain_prompt)

    print(f"  {B}MetaGenesis:{X}")
    for line in response1.split("\n"):
        print(f"  {line}")
    print()

    # ---- Step 2: Run verification ----
    print(f"  {C}[Step 2/3]{X} Running verification...")
    print(f"  {DIM}Executing {claim} for domain '{domain}'...{X}")
    print()

    try:
        claim_result = run_claim(domain)
        claim_passed = claim_result.get("result", {}).get("pass", False)

        # Create bundle
        bundle_dir = create_bundle(
            claim_result,
            output_dir=str(REPO_ROOT / "_onboard_bundle" / session_hash),
        )

        # Verify all 5 layers
        all_passed, layer_results = verify_bundle(bundle_dir)

        # Print layer results
        print(f"  {B}Verification Results{X}")
        print(f"  {'=' * 50}")
        for name, ok, detail in layer_results:
            icon = f"{G}PASS{X}" if ok else f"{R}FAIL{X}"
            print(f"  [{icon}] {name}")
            print(f"         {DIM}{detail}{X}")
        print(f"  {'=' * 50}")
        print()

    except Exception as e:
        print(f"  {R}Verification error:{X} {e}")
        all_passed = False
        claim_passed = False
        layer_results = []
        bundle_dir = None

    # Get Claude's explanation of results
    if all_passed:
        result_prompt = (
            f"The verification PASSED for domain {domain} (claim {claim}). "
            f"All 5 layers verified successfully. "
            f"Explain this result to the user in their language. "
            f"Emphasize: their computation is now cryptographically certified, "
            f"tamper-evident, and independently verifiable by any third party "
            f"with one command. Mention the physical anchor if applicable. "
            f"Then present the $299 bundle offer with Stripe link: {STRIPE_LINK} "
            f"and explain what they get for $299 (permanent bundle, receipt, "
            f"third-party verification). Keep it under 200 words."
        )
    else:
        result_prompt = (
            f"The verification FAILED for domain {domain} (claim {claim}). "
            f"Explain to the user in their language what went wrong and "
            f"suggest how to fix it. Mention that a free pilot is available "
            f"at {PILOT_URL} or by emailing {CONTACT_EMAIL}. "
            f"Keep it under 150 words."
        )

    if mock_mode:
        response2 = _mock_call(client, messages, result_prompt)
    else:
        response2 = _call_claude(client, messages, result_prompt)

    # ---- Step 3: Show result and payment ----
    print(f"  {C}[Step 3/3]{X} {'Verification complete!' if all_passed else 'Verification needs attention'}")
    print()
    print(f"  {B}MetaGenesis:{X}")
    for line in response2.split("\n"):
        print(f"  {line}")
    print()

    if all_passed:
        print(f"  {G}{B}  VERIFICATION: PASS  {X}")
        print()
        print(f"  {B}Get your permanent verification bundle:{X}")
        print(f"  {C}{STRIPE_LINK}{X}")
        print(f"  {DIM}$299 -- one-time -- includes receipt + third-party verification{X}")
    else:
        print(f"  {R}{B}  VERIFICATION: FAIL  {X}")
        print()
        print(f"  {B}Free pilot available:{X}")
        print(f"  {C}{PILOT_URL}{X}")
        print(f"  {DIM}Or email: {CONTACT_EMAIL}{X}")

    print()

    # Log session
    _log_session(domain, claim, language, all_passed, user_description, session_hash)

    # Track in payment funnel
    try:
        from scripts.mg_payment_tracker import track_event
        track_event("started_onboarding", domain=domain, language=language,
                    session_hash=session_hash)
        if all_passed:
            track_event("completed_verification", domain=domain, language=language,
                        session_hash=session_hash)
            track_event("saw_payment", domain=domain, language=language,
                        session_hash=session_hash)
    except ImportError:
        pass  # payment tracker not yet available

    # Clean up bundle
    if bundle_dir and Path(bundle_dir).exists():
        import shutil
        shutil.rmtree(bundle_dir, ignore_errors=True)

    return {
        "domain": domain,
        "claim": claim,
        "passed": all_passed,
        "language": language,
        "session_hash": session_hash,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="mg_onboard",
        description="MetaGenesis Core -- Multilingual Client Onboarding",
        epilog=(
            "Examples:\n"
            "  python scripts/mg_onboard.py --api-key sk-ant-...\n"
            "  ANTHROPIC_API_KEY=sk-ant-... python scripts/mg_onboard.py\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--api-key", type=str, default=None,
        help="Anthropic API key (or set ANTHROPIC_API_KEY env var)",
    )

    args = parser.parse_args()
    api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        print(f"{R}ERROR:{X} No API key provided.")
        print(f"  Use --api-key YOUR_KEY or set ANTHROPIC_API_KEY env var")
        return 1

    result = run_onboarding(api_key)
    if result is None:
        return 1
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
