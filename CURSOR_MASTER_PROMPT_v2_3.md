# MetaGenesis Core — Cursor Master Prompt v2.3
**Версия:** 2.3 | **Дата:** 2026-03-16
**Использовать:** как шаблон для КАЖДОГО промта Cursor

---

## БЛОК A — ВСТАВЛЯТЬ В НАЧАЛО КАЖДОГО ПРОМТА (обязательно)

```
CONTEXT: MetaGenesis Core — verification protocol layer for computational claims.
PPA #63/996,819. Repo: https://github.com/Lama999901/metagenesis-core-public

NEVER TOUCH these files under any circumstances:
  - scripts/steward_audit.py         ← SEALED (CI-locked)
  - scripts/mg.py
  - scripts/mg_policy_gate_policy.json
  - tests/steward/test_cert02_pack_includes_evidence_and_semantic_verify.py
  - ppa/CLAIMS_DRAFT.md
  - .github/workflows/ (add only, never delete)

BANNED TERMS — never write these anywhere:
  "tamper-proof" / "GPT-5" / "19x performance" / "VacuumGenesisEngine"
  "unforgeable" / "100% test success" / "500+ modules" / "Infinity Protocol"
  "blockchain" (use: "cryptographic hash chain" / "Step Chain Verification")
  Instead use: "tamper-evident under trusted verifier assumptions"

CURRENT STATE:
  14 claims / 223 tests / 3 verification layers / MVP v0.2
  steward_audit: PASS / deep_verify: ALL 10 TESTS PASSED
```

---

## БЛОК B — ШАБЛОН ДЛЯ ИЗМЕНЕНИЙ В index.html (сайт)

```
Make exactly N changes to index.html. Nothing else.
DO NOT touch any Python files, CSS, or JavaScript.

CHANGE 1
Find exactly:
  <точная строка из файла>
Replace with:
  <новая строка>

Verify after:
  grep "ключевое_слово" index.html  → must return N results
```

**ВАЖНЫЕ ПРАВИЛА для index.html:**
- Читай файл ПЕРЕД правкой — всегда свежее чтение
- Точные строки — Cursor делает find/replace побуквенно
- Внешние ссылки → `target="_blank"`
- Ссылки на claim файлы: `https://github.com/Lama999901/metagenesis-core-public/blob/main/`
- Не трогать CSS классы и JS

---

## БЛОК C — ШАБЛОН ДЛЯ ИЗМЕНЕНИЙ В PYTHON/DOCS

```
Fix exactly these N issues. Nothing else.

ISSUE 1 — <описание>
FILE: <путь>
  Find:    <старая строка>
  Replace: <новая строка>

DO NOT TOUCH:
  - scripts/steward_audit.py
  - scripts/mg.py
  - scripts/mg_policy_gate_policy.json
  - tests/steward/test_cert02_*
  - ppa/CLAIMS_DRAFT.md

After all changes:
  python scripts/steward_audit.py   # → STEWARD AUDIT: PASS
  python -m pytest tests/ -q        # → 223 passed (или больше)
  python scripts/deep_verify.py     # → ALL 10 TESTS PASSED
```

---

## БЛОК D — ШАБЛОН ДЛЯ НОВОГО CLAIM (6 шагов)

```
Add a new verification claim. Follow ALL 6 steps exactly.

CLAIM: <CLAIM_ID>
DOMAIN: <домен>
JOB_KIND: <job_kind_string>
THRESHOLD: <метрика> ≤ <значение>

STEP 1 — Implementation
CREATE: backend/progress/<claim_id_lower>.py
  - JOB_KIND = "<job_kind_string>"
  - ALGORITHM_VERSION = "v1"
  - def run_<claim>() → dict with mtr_phase key
  - execution_trace + trace_root_hash (Step Chain — 4 steps)
  - Stdlib only, deterministic with seed

STEP 2 — Runner dispatch
FILE: backend/progress/runner.py
  Add dispatch block for job_kind == "<job_kind_string>"

STEP 3 — Claim index
FILE: reports/scientific_claim_index.md
  Add section with: claim_id, domain, job_kind (backticks), V&V thresholds

STEP 4 — Canonical state
FILE: reports/canonical_state.md
  Add <CLAIM_ID> to current_claims_list

STEP 5 — Tests (minimum 3)
CREATE: tests/<domain>/test_<claim_id_lower>.py
  - test_pass, test_fail, test_runner

STEP 6 — Update numbers
  index.html: N → N+1 claims
  system_manifest.json: add to active_claims
  README.md, AGENTS.md, llms.txt: update counts

After:
  python scripts/steward_audit.py   → PASS
  python -m pytest tests/ -q        → all passed
  python scripts/deep_verify.py     → ALL 10 TESTS PASSED
```

---

## БЛОК E — КАРТА CLAIM → ФАЙЛЫ

```
MTR-1        → backend/progress/mtr1_calibration.py
MTR-2        → backend/progress/mtr2_thermal_conductivity.py
MTR-3        → backend/progress/mtr3_thermal_multilayer.py
SYSID-01     → backend/progress/sysid1_arx_calibration.py
DATA-PIPE-01 → backend/progress/datapipe1_quality_certificate.py
DRIFT-01     → backend/progress/drift_monitor.py
ML_BENCH-01  → backend/progress/mlbench1_accuracy_certificate.py  ← real data mode ✅
DT-FEM-01    → backend/progress/dtfem1_displacement_verification.py ← real data mode ✅
ML_BENCH-02  → backend/progress/mlbench2_regression_certificate.py
ML_BENCH-03  → backend/progress/mlbench3_timeseries_certificate.py
PHARMA-01    → backend/progress/pharma1_admet_certificate.py
FINRISK-01   → backend/progress/finrisk1_var_certificate.py
DT-SENSOR-01 → backend/progress/dtsensor1_iot_certificate.py
DT-CALIB-LOOP-01 → backend/progress/dtcalib1_convergence_certificate.py
```

BASE URL: `https://github.com/Lama999901/metagenesis-core-public/blob/main/`

---

## БЛОК F — CSS ПЕРЕМЕННЫЕ САЙТА

```css
--ink:#04081a  --ink1:#070c1f  --ink2:#0b1226
--c:#00e5ff   --ok:#00ff99   --err:#ff4060
--txt:#eef7fb  --fd:'Unbounded'  --fm:'IBM Plex Mono'
```
**Formspree ID:** `xlgpdwop`
**Payment:** email yehor@metagenesis-core.dev (bank transfer / crypto / invoice)

---

## БЛОК G — СТРУКТУРА САЙТА

```
<nav>     Protocol | Claims | Verticals | For You | Verify | Free Pilot | GitHub
#hero     — 14 claims, 223 tests, AUDIT: PASS
#protocol — "Not a tool. A standard." — 4 инновации + Step Chain
#claims   — 14 claim карточек с ссылками
#verticals — 6 вертикалей
#crisis   — статистика кризиса воспроизводимости
#compare  — сравнение (MetaGenesis vs MLflow vs DVC vs Trust PDF)
#regulatory — "Three Deadlines" (EU AI Act / FDA / Basel)
#pricing  — OSS / Free Pilot / Bundle $299 / Enterprise
#faq      — 5 вопросов
#segments — 4 таба (ML/AI, Pharma, Finance, Research)
#verifier — Live Verifier
#pilot    — Free Pilot Form (Formspree: xlgpdwop)
.cband    — CTA
<footer>
```

**Hero badge:** `14 active claims | 223 tests | PASS | patent pending`

---

## БЛОК H — ПРОВЕРКА ПОСЛЕ ИЗМЕНЕНИЙ САЙТА

```powershell
# Числа в index.html
Select-String "223" index.html   # → 9+ мест
Select-String "14" index.html    # → 3+ мест

# JavaScript проверка в браузере
const sections = ['protocol','claims','verticals','crisis','compare',
  'regulatory','pricing','faq','segments','verifier','pilot']
  .map(id => id+':'+(document.getElementById(id)?'✅':'❌')).join(' | ')
const broken = Array.from(document.querySelectorAll('a[href^="#"]'))
  .filter(a => {const id=a.getAttribute('href').substring(1); return id&&!document.getElementById(id);})
  .map(a => a.getAttribute('href')).join(',') || 'none'
sections + '\nBROKEN: ' + broken
```

---

## БЛОК I — GIT WORKFLOW

```powershell
# 1. Всегда новая ветка
git checkout -b fix/описание

# 2. Внести изменения

# 3. Проверить числа перед коммитом
Select-String "СТАРОЕ_ЧИСЛО" index.html, README.md, llms.txt, CONTEXT_SNAPSHOT.md, system_manifest.json

# 4. Запустить тесты
python scripts/steward_audit.py    # → PASS
python -m pytest tests/ -q         # → all passed
python scripts/deep_verify.py      # → ALL 10 TESTS PASSED

# 5. Коммит и пуш
git add <файлы>
git commit -m "type: описание"
git push origin fix/описание
# → PR → CI PASS → merge → Vercel auto-deploy
```

**TRAP:** main защищён — прямой push заблокирован. Всегда через ветку + PR.

---

## БЛОК J — ЧАСТЫЕ ПРОБЛЕМЫ

| Проблема | Решение |
|---------|---------|
| edit_file не находит строку | Читай файл ПЕРЕД правкой — не из кэша |
| steward_audit → FAIL | Новый claim не в canonical_state или runner |
| Числа не совпадают | grep по всем файлам перед коммитом |
| Push rejected | git stash → pull --no-rebase → stash pop → push |
| Windows cp1252 emoji | io.TextIOWrapper encoding='utf-8' |
| write_file большой файл | Только edit_file с точными строками |

---

## БЛОК K — locked_paths (актуально)

**`scripts/mg_policy_gate_policy.json` содержит 3 locked_paths:**
```
reports/canonical_state.md
demos/open_data_demo_01/evidence_index.json
scripts/steward_audit.py
```

---

## БЛОК L — REAL DATA MODE (добавлен 2026-03-16)

### Что такое real data mode

Два claim типа поддерживают верификацию реальных данных клиента:
```
ML_BENCH-01  → mlbench1_accuracy_certificate.py  (параметр dataset_relpath)
DT-FEM-01    → dtfem1_displacement_verification.py (параметр dataset_relpath)
```

Если `dataset_relpath` задан — synthetic mode выключается, данные читаются из CSV клиента.

### CSV форматы

**ML_BENCH-01** — классификация:
```
y_true,y_pred
1,1
0,0
1,0
...
```
Минимум 10 строк. Целые числа 0/1.

**DT-FEM-01** — FEM vs физические измерения:
```
fem_value,measured_value,quantity
12.10,12.00,displacement_mm
85.20,84.00,temperature_celsius
...
```
Колонка `quantity` — опциональная.

### Runner payload для real data

```python
# ML_BENCH-01
payload = {
    "kind": "mlbench1_accuracy_certificate",
    "claimed_accuracy": 0.942,
    "accuracy_tolerance": 0.02,
    "dataset_relpath": "reports/client_data/client_predictions.csv",
}

# DT-FEM-01
payload = {
    "kind": "dtfem1_displacement_verification",
    "rel_err_threshold": 0.02,
    "dataset_relpath": "reports/client_data/client_fem_results.csv",
}
```

### CSV фикстуры для тестов

```
tests/fixtures/ml_bench01_pass.csv    — 100 строк, 90% accuracy → PASS
tests/fixtures/ml_bench01_fail.csv    — 100 строк, ~60% accuracy → FAIL
tests/fixtures/ml_bench01_minimal.csv — 10 строк, 100% → PASS
tests/fixtures/dtfem01_pass.csv       — 5 строк, все rel_err < 2% → PASS
tests/fixtures/dtfem01_fail.csv       — 5 строк, одна строка 20% error → FAIL
```

### Тесты real data mode

```
tests/ml/test_mlbench01_realdata.py          — ML_BENCH-01 real data
tests/digital_twin/test_dtfem01_realdata.py  — DT-FEM-01 real data
tests/cli/test_real_data_e2e.py              — full runner e2e цикл
```

**Acceptance команды:**
```bash
python -m pytest tests/ml/test_mlbench01_realdata.py -v
python -m pytest tests/digital_twin/test_dtfem01_realdata.py -v
python -m pytest tests/cli/test_real_data_e2e.py -v
python scripts/deep_verify.py  # → ALL 10 TESTS PASSED
```

### Отличие real data bundle от synthetic

| | Synthetic mode | Real data mode |
|---|---|---|
| `execution_trace` | ✅ есть | ❌ нет |
| `trace_root_hash` | ✅ есть | ❌ нет |
| `inputs.dataset.sha256` | ❌ нет | ✅ есть |
| `inputs.dataset.rows` | ❌ нет | ✅ есть |
| Tamper evidence | Step Chain | Dataset SHA-256 |

### Путь первого клиентского bundle

```
1. Клиент присылает CSV на yehor@metagenesis-core.dev
2. Сохранить: reports/client_data/<name>.csv
3. Запустить через runner с dataset_relpath
4. mg.py pack build → bundle.zip
5. Клиент: python mg.py verify --pack bundle.zip → PASS
```

**Полный гайд:** `docs/REAL_DATA_GUIDE.md`

### ВАЖНО при добавлении real data mode в новый claim

1. Добавить `_load_<type>_csv(path)` функцию
2. Добавить `from backend.progress.data_integrity import fingerprint_file`
3. Вернуть `inputs.dataset` с sha256, bytes, rows
4. НЕ добавлять execution_trace в real data branch
5. Написать тест в `tests/<domain>/test_<claim>_realdata.py`
6. Добавить фикстуру в `tests/fixtures/`

---

## БЛОК M — KNOWN TRAPS (топ-10)

```
TRAP-01: ZIP папка ≠ git репо
  Только: C:\Users\999ye\Downloads\metagenesis-core-public\

TRAP-03: Числа в 9+ местах в index.html
  ВСЕГДА grep ПЕРЕД коммитом

TRAP-08: Gmail вместо Zoho
  Все outreach только из yehor@metagenesis-core.dev

TRAP-13: Direct push в main заблокирован
  Всегда ветка + PR

TRAP-14: Windows cp1252 не печатает emoji
  io.TextIOWrapper encoding='utf-8'

TRAP-NEW-06: write_file на большой файл → пробел
  Только edit_file с точными строками

TRAP-NEW-07: Email без проверки → bounce
  Всегда проверять email через сайт человека

TRAP-NEW-08: edit_file из кэша → строка не найдена
  Читай файл свежим чтением ПЕРЕД каждым edit
```

---

*CURSOR_MASTER_PROMPT v2.3 — 2026-03-16 — MetaGenesis Core*
*Изменения: добавлен БЛОК L (real data mode), БЛОК M (traps), обновлены числа 14/223*
