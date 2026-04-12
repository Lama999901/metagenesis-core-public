# MetaGenesis Core -- Quick Start

MetaGenesis Core is a verification protocol that makes computational results tamper-evident and independently auditable. One command tells you if an evidence bundle is authentic: `PASS` or `FAIL`.

**Version:** v0.9.0 | **Tests:** 2405 | **Claims:** 20 | **License:** MIT | **Patent:** USPTO #63/996,819

---

## 1. Install

```bash
git clone https://github.com/Lama999901/metagenesis-core-public.git
cd metagenesis-core-public
pip install -r requirements.txt
```

Python 3.9+ required. No external services, no API keys, no GPU.

---

## 2. Try it

```bash
python scripts/mg_demo.py
```

Pick a domain (ML, pharma, finance, materials, digital twin). The demo runs a real claim, creates a signed bundle, and verifies all 5 layers. You will see `PASS` or `FAIL`.

Or use the client CLI directly:

```bash
python scripts/mg_client.py --demo
```

---

## 3. Verify an existing bundle

```bash
python scripts/mg.py verify --pack <bundle_directory>
```

This checks all 5 verification layers:
- **Layer 1** -- SHA-256 integrity (file modification detection)
- **Layer 2** -- Semantic verification (evidence stripping detection)
- **Layer 3** -- Step Chain (computation input/order tampering detection)
- **Layer 4** -- Bundle Signing (unauthorized creator detection)
- **Layer 5** -- Temporal Commitment (backdating detection)

If any layer fails, the bundle is compromised. No partial passes.

---

## 4. Create a bundle for your data

```bash
python scripts/mg_client.py --domain ml --data your_params.json
```

Supported domains: `ml`, `pharma`, `finance`, `materials`, `digital_twin`

For a full walkthrough, see [docs/CLIENT_GUIDE.md](CLIENT_GUIDE.md).

---

## 5. Get a verified bundle for your organization

**Entry price:** $299 per verified bundle.

We run your computation through the protocol, produce a signed evidence bundle, and you get an independently verifiable artifact -- no trust required.

**Contact:** [yehor@metagenesis-core.dev](mailto:yehor@metagenesis-core.dev)
**Pilot program:** [metagenesis-core.dev/#pilot](https://metagenesis-core.dev/#pilot)

---

## Learn more

- [CLIENT_GUIDE.md](CLIENT_GUIDE.md) -- Full client onboarding guide
- [PROTOCOL.md](PROTOCOL.md) -- Protocol specification
- [ARCHITECTURE.md](ARCHITECTURE.md) -- System architecture
- [../SECURITY.md](../SECURITY.md) -- Threat model and verification guarantees
