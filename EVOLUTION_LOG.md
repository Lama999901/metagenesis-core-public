# MetaGenesis Core — Evolution Log v4.0
> Живой мозг проекта. Читается ПЕРВЫМ в каждом новом чате.
> Обновлён: 2026-03-15 (конец большой сессии аудита и достройки)

---

## ══ CURRENT STATE ══

```
claims:              14
tests:               223 passing
verification_layers: 3 (integrity + semantic + step chain)
domains:             7
steward_audit:       PASS
ci:                  GREEN
git:                 CLEAN (0 open PRs, 0 uncommitted after last push)
site:                metagenesis-core.dev — 14/223/3/7 LIVE
protocol:            MVP v0.2
deep_verify:         ALL 10 TESTS PASSED (proof, not trust)
stripe:              $299 — https://buy.stripe.com/14AcN57qH19R1qN3QQ6Na00
hn_post:             https://news.ycombinator.com/item?id=47335416
github_release:      v0.1.0 (v0.2.0 PENDING)
```

---

## ══ LAST SESSION — 2026-03-16 (outreach + site + repo audit) ══

### Что сделали:
1. **Site full update** — PR #98 смержен, задеплоен на Vercel
2. **Problem section** переписан → "The Verification Gap", proof strip с 5 тест-ссылками
3. **Regulatory section** → "Three Deadlines", claim chips с ссылками, deadline badges
4. **sec-dark backdrop** на 3 секциях (pitch, regulatory, segments)
5. **Origin section** полностью переписан — новая цитата, stats 5/223/14/1, 4 шага с proof links
6. **Payment** — убран Stripe, заменён на email + bank/crypto/invoice
7. **Sharp edges fix** — sec-dark inset увеличен, regrid/proof-strip border-radius
8. **Protocol h2** → "Not a tool. A standard."
9. **v0.2.0 Release** создан на GitHub
10. **19 писем** отправлено из Zoho — коммерческие + академики по всему миру
11. **Anthropic OSS Program** — форма подана
12. **Anthropic Partner Network** — contact sales форма подана
13. **Repo audit 100%** — llms.txt, CONTEXT_SNAPSHOT, COMMERCIAL обновлены
14. **GitHub topics** — нужно добавить вручную через Settings

### Косяки (не повторять):
- TRAP-NEW-06: write_file на большой файл → перезаписал пробелом → потребовал git checkout
- TRAP-NEW-07: email sayash@princeton.edu неверный → правильный sayashk@princeton.edu → проверять через сайт
- TRAP-NEW-08: edit_file из кэша вместо свежего чтения → несовпадение строк

### Остановились на:
- index.html изменения НЕ запушены в отдельном коммите (payment + sharp edges + protocol h2)
- PR #98 смержен но новые правки ещё в working directory

### Следующий шаг:
```
git add index.html llms.txt CONTEXT_SNAPSHOT.md COMMERCIAL.md
git commit -m "feat: payment email/crypto, sharp edges, protocol h2, regulatory overhaul"
git push origin main  # или через новый PR
```

---

## ══ LAST SESSION — 2026-03-15 (полный аудит + достройка) ══

### Что построили:
1. **Step Chain во всех 14 claims** — execution_trace + trace_root_hash везде
2. **Cross-Claim Cryptographic Chain** — MTR-1 → DT-FEM-01 → DRIFT-01 через anchor_hash
3. **6 новых claims** — ML_BENCH-02/03, PHARMA-01, FINRISK-01, DT-SENSOR-01, DT-CALIB-LOOP-01
4. **deep_verify.py** — 10-тестовый proof-not-trust скрипт в scripts/
5. **verify-chain CLI** — mg.py verify-chain bundle1/ bundle2/ bundle3/
6. **anchor_hash validation** в mg.py verify

### Что зачистили (доля полного аудита):
- MVP v0.1 → v0.2 синхронизировано в 22 backend/scripts/tests файлах
- AGENTS.md таблица 8→14 claims
- ARCHITECTURE.md 8→14 claims, 153→223 tests
- ROADMAP.md PHARMA/FINRISK/DT отмечены ✓, MVP v0.1→v0.2
- known_faults.yaml 153→223
- CLAIMS_DRAFT_v2 147→223 + 6 новых claims добавлены в таблицу
- USPTO_PPA_TEXT 91→223 + amendment note 2026-03-15
- system_manifest.json protocol v0.1→v0.2
- .gitignore: reports/ledger_snapshots/, reports/progress_runs/ добавлены
- policy gate: FUNDING.yml добавлен в allowlist
- test_step_chain_all_claims.py docstring 8→14
- CONTEXT_SNAPSHOT: What is done секция добавлена, стейлы убраны
- PROTOCOL.md дата 2026-03-14→2026-03-15

### Найденные ловушки (не повторять):
- **TRAP-NEW-01:** Windows cp1252 не печатает emoji в subprocess.run → fix: `io.TextIOWrapper(..., encoding='utf-8')`
- **TRAP-NEW-02:** deep_verify сам себя проверял на forbidden terms → fix: `if f.name == "deep_verify.py": continue`
- **TRAP-NEW-03:** .gitignore не содержал reports/ledger_snapshots/ и reports/progress_runs/ → исправлено
- **TRAP-NEW-04:** FUNDING.yml не был в policy gate allowlist → исправлено
- **TRAP-NEW-05:** final_sweep.py и debug_t9.py оставались на диске — в .gitignore они защищены, но лучше удалять вручную

---

## ══ VERIFIED ARCHITECTURE ══

```
14 CLAIMS:
  MTR-1/2/3     → materials science (physical anchor E=70 GPa)
  SYSID-01      → ARX system identification
  DATA-PIPE-01  → data pipeline quality
  DRIFT-01      → drift monitoring (MTR-1 anchor)
  ML_BENCH-01   → ML classification accuracy + Step Chain
  DT-FEM-01     → digital twin / FEM (MTR-1 anchor)
  ML_BENCH-02   → ML regression (RMSE, MAE, R²)
  ML_BENCH-03   → ML time-series (MAPE)
  PHARMA-01     → ADMET prediction (FDA 21 CFR Part 11)
  FINRISK-01    → VaR model (Basel III/IV)
  DT-SENSOR-01  → IoT sensor integrity
  DT-CALIB-LOOP-01 → calibration convergence (DRIFT-01 anchor)

3 VERIFICATION LAYERS:
  Layer 1 — SHA-256 integrity      → test_cert01
  Layer 2 — Semantic bypass attack → test_cert02 (LIVE PROVED in deep_verify)
  Layer 3 — Step Chain             → test_cert03

CROSS-CLAIM CHAIN:
  E=70GPa → MTR-1.trace_root_hash → anchor_hash in DT-FEM-01 → anchor_hash in DRIFT-01
  PROVED: tests/steward/test_cross_claim_chain.py

5 PATENTABLE INNOVATIONS:
  1. Bidirectional Claim Coverage    → steward_audit.py
  2. Tamper-Evident Semantic Bundle  → mg.py _verify_semantic()
  3. Policy-Gate Immutable Anchors   → mg_policy_gate_policy.json
  4. Dual-Mode Canary Pipeline       → runner.py run_job(canary_mode=)
  5. Step Chain + Cross-Claim Chain  → all 14 claims + anchor_hash

LOCKED PATHS (3):
  reports/canonical_state.md
  demos/open_data_demo_01/evidence_index.json
  scripts/steward_audit.py
```

---

## ══ KEY FILES MAP ══

```
PROOF:
  scripts/deep_verify.py         — 10-test proof script (RUN THIS FIRST)
  scripts/steward_audit.py       — governance (SEALED)
  scripts/mg.py                  — pack build + verify (3 layers) + verify-chain
  tests/steward/test_cert02_*    — bypass attack proof
  tests/steward/test_cert03_*    — step chain proof
  tests/steward/test_cross_claim_chain.py — cross-claim proof

CLAIMS:
  backend/progress/runner.py     — all 14 dispatched
  backend/progress/<claim>.py    — 14 implementations
  reports/scientific_claim_index.md — all 14 with thresholds
  reports/canonical_state.md    — LOCKED authoritative list

DOCS (all synced to v0.2):
  CONTEXT_SNAPSHOT.md            — READ FIRST (AI agents)
  AGENTS.md                      — rules + 14 claims table
  llms.txt                       — AI-optimized summary
  README.md                      — public face
  docs/PROTOCOL.md               — v0.2 spec
  docs/ARCHITECTURE.md           — v0.2 diagrams + 14 claims
  docs/ROADMAP.md                — v0.2, done/pending
  docs/HOW_TO_ADD_CLAIM.md       — Step Chain required
  docs/USE_CASES.md              — 8 domains
  ppa/CLAIMS_DRAFT_v2.md         — all 9 post-filing claims
  ppa/USPTO_PPA_TEXT.md          — amendment 2026-03-15, 223 tests

SITE:
  index.html                     — 14/223/3/7 LIVE ✅
```

---

## ══ PENDING TASKS (приоритет ↓) ══

### 🔴 GIT (прямо сейчас)
- [ ] Push branch `docs/agents-claims-protocol-final` → merge PR (не попал в main напрямую)
  ```
  git push origin docs/agents-claims-protocol-final
  ```

### 🟡 RELEASE
- [ ] GitHub Release v0.2.0 — создать тег после всех PRов в main

### 🟡 OUTREACH (эта неделя)
- [ ] Elena Samuylova — resend WITH subject → founders@evidentlyai.com
- [ ] Anand Kannappan → anand@patronus.ai
- [ ] Vikram Chatterji → vikram@galileo.ai
- [ ] Woody Sherman → woody.sherman@psithera.com
- [ ] Jonathan Godwin → jonathan@orbitalmaterials.com (verify email)
- ⚠️ ВСЕ из Zoho (yehor@metagenesis-core.dev), НЕ Gmail

### 🟢 COMMUNITY
- [ ] r/MachineLearning post
- [ ] MLOps Community Slack → #tools-and-frameworks
- [ ] Twitter/X — Step Chain bypass attack hook

### 🟢 LEGAL
- [ ] Patent attorney для non-provisional (deadline 2027-03-05, бюджет $3K-8K)

### 🟢 COMMERCIAL
- [ ] First paying customer ($299)

---

## ══ VERIFICATION COMMANDS ══

```bash
# Быстрая проверка
python scripts/steward_audit.py      # → STEWARD AUDIT: PASS
python -m pytest tests/ -q           # → 223 passed

# Полная проверка (proof, not trust)
python scripts/deep_verify.py        # → ALL 10 TESTS PASSED

# Demo
python demos/open_data_demo_01/run_demo.py  # → PASS PASS

# Git чистота
git status --porcelain               # → пусто
```

---

## ══ KNOWN TRAPS (полный список) ══

```
TRAP-01: ZIP папка ≠ git репо
  Только: C:\Users\999ye\Downloads\metagenesis-core-public\
  НЕ zip-копии

TRAP-02: locked_paths deadlock при новом claim
  Workflow: unlock PR → add claim → relock PR

TRAP-03: Числа в 9+ местах в index.html + 6 docs файлах
  ВСЕГДА grep ПЕРЕД коммитом

TRAP-04: git push на неправильную ветку
  git branch → звёздочка → git push origin <ТО_ЧТО_СО_ЗВЁЗДОЧКОЙ>

TRAP-05: Remote ahead при push
  git stash → git pull --no-rebase → git stash pop → git push

TRAP-06: Старый index.html в Claude /uploads
  Filesystem:copy_file_user_to_claude ПЕРЕД аудитом сайта

TRAP-07: "Step Chain" = блокчейн
  НЕТ. Hash chain offline без сети. Не называть блокчейном.

TRAP-08: Gmail вместо Zoho
  Все письма только из yehor@metagenesis-core.dev (Zoho)

TRAP-09: Публичное заявление без проверки кода
  Сначала читаю код → убеждаюсь → пишу

TRAP-10: Числа в 12+ местах
  PowerShell Select-String перед каждым коммитом

TRAP-11: locked_paths = 5 (устаревшее)
  РЕАЛЬНО: 3 пути. Проверять mg_policy_gate_policy.json

TRAP-12: Лимит инструментов за ход
  Батчи по 3-4 файла. Один JS вызов для сайта.

TRAP-13: Main защищён — прямой push заблокирован
  Всегда через ветку + PR → CI PASS → merge

TRAP-14: Windows cp1252 не печатает emoji
  В Python скриптах: sys.stdout = io.TextIOWrapper(..., encoding='utf-8')

TRAP-15: Скрипт проверяет сам себя на forbidden terms
  Добавлять: if f.name == "deep_verify.py": continue

TRAP-16: reports/ledger_snapshots/ и progress_runs/ не в .gitignore
  ИСПРАВЛЕНО — теперь в .gitignore

TRAP-17: FUNDING.yml не в policy gate allowlist
  ИСПРАВЛЕНО — добавлен ".github/FUNDING.yml" в allow_globs
```

---

## ══ WORKFLOW ДЛЯ НОВОГО ЧАТА ══

```
НАЧАЛО СЕССИИ:
  1. Читаю EVOLUTION_LOG.md (этот файл) → CURRENT STATE
  2. Читаю CONTEXT_SNAPSHOT.md → что pending
  3. Смотрю KNOWN TRAPS → не повторяю ошибки
  4. Запускаю: python scripts/deep_verify.py → ALL 10 TESTS PASSED
  5. Если не PASS — сначала чиним, потом работаем

КОНЕЦ СЕССИИ:
  1. git status --porcelain → пусто (всё закоммичено)
  2. Обновляю CURRENT STATE в этом файле
  3. Добавляю LAST SESSION → что сделали
  4. Обновляю PENDING TASKS → [x] выполненные
  5. Новые ловушки → KNOWN TRAPS
  6. Загружаю в Claude Projects

ПРАВИЛА РАБОТЫ С КОДОМ:
  - Читаю файл ДО правки, не после
  - Не изменяю sealed файлы: steward_audit.py, test_cert02_*
  - После каждого изменения → steward_audit PASS
  - Перед merge → deep_verify ALL 10 PASSED
  - В репо только через ветку + PR, никогда direct push в main
```

---

## ══ SESSION LOG ══

| Дата | Что сделано | Claims | Tests |
|------|------------|--------|-------|
| 2026-03-05 | PPA filed | 5 | 39 |
| 2026-03-09 | DRIFT-01, ML_BENCH-01 | 7 | 91 |
| 2026-03-10 | steward_audit CI-sealed | 7 | 91 |
| 2026-03-11 | DT-FEM-01 | 8 | 107 |
| 2026-03-12 | PRs #26 #31 merged | 8 | 107 |
| 2026-03-13 | HN live, Physical Anchor, SCOPE_001 | 8 | 107 |
| 2026-03-14 утро | Step Chain ML_BENCH-01, v0.1.0 release | 8 | 113 |
| 2026-03-14 вечер | mg.py verify Step Chain, test_cert03, 3 layers | 8 | 118 |
| 2026-03-15 | Summits 1-8: 6 new claims, Cross-Chain, deep_verify, full audit | 14 | 223 |

---

---

## ТЕКУЩЕЕ СОСТОЯНИЕ (конец сессии 2026-03-18)

```
claims:   14 | tests: 526 | layers: 5 | innovations: 8
v0.5.0 — PRs запушены, мёрж pending
CLAUDE.md v2.0 — конфликт resolved
agent_learn.py + agent_evolution.py — готовы
```

## СЛЕДУЮЩИЙ ШАГ

```
1. Смержить PRs на GitHub (phase-05, 07, 08)
2. GitHub Release v0.5.0
3. python scripts/agent_learn.py observe
4. Submit JOSS paper
5. /gsd:quick "Sync docs to v0.5.0: 8 innovations, CERT-11/12"
```

*EVOLUTION_LOG — обновлён 2026-03-18*
