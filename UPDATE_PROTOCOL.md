# MetaGenesis Core — Update Protocol
> Версия 1.0 — 2026-03-16
> Обязательный чеклист при каждом значительном изменении.
> Цель: репо, сайт, документация и Project Knowledge всегда синхронны.

---

## ПРИНЦИП

Каждое значительное изменение затрагивает несколько слоёв одновременно.
Не обновить все слои = хвост который накапливается и ломает доверие.

**Значительное изменение** = любое из:
- Новый claim добавлен
- Тесты добавлены/изменены (счётчик меняется)
- Новый verification layer
- Новая патентная инновация
- Изменение способа оплаты / ценообразования
- Новый домен или вертикаль
- Значительный outreach (≥5 писем)
- Новый публичный релиз
- Изменение архитектуры протокола

---

## ЧЕКЛИСТ ПО ТИПУ ИЗМЕНЕНИЯ

---

### 📦 НОВЫЙ CLAIM

```
[ ] backend/progress/<claim_id>.py — реализация
[ ] runner.py — dispatch добавлен
[ ] reports/scientific_claim_index.md — секция добавлена
[ ] reports/canonical_state.md — claim_id в current_claims_list

[ ] ЧИСЛА ОБНОВИТЬ ВЕЗДЕ:
    [ ] system_manifest.json → active_claims + test_count
    [ ] index.html → N claims (hero badge + claims grid + pricing)
    [ ] README.md → badges + claims table + verification state
    [ ] AGENTS.md → acceptance commands test count
    [ ] llms.txt → active claims list + current state counts
    [ ] CONTEXT_SNAPSHOT.md → verified state table
    [ ] ppa/README_PPA.md → post-filing additions table
    [ ] CURSOR_MASTER_PROMPT_v2_X.md → БЛОК E карта файлов

[ ] ТЕСТЫ:
    [ ] tests/<domain>/test_<claim_id>.py — минимум: pass, fail, runner
    [ ] python scripts/steward_audit.py → PASS
    [ ] python -m pytest tests/ -q → все прошли
    [ ] python scripts/deep_verify.py → ALL 10 PASSED

[ ] PROJECT KNOWLEDGE ОБНОВИТЬ:
    [ ] EVOLUTION_LOG.md → CURRENT STATE + SESSION LOG
    [ ] CLAUDE_PROJECT_MASTER → claims table + numbers
    [ ] NEXT_CHAT_PRIMER → pending tasks
```

**Grep перед коммитом:**
```powershell
Select-String "СТАРОЕ_N claims" index.html, README.md, llms.txt, CONTEXT_SNAPSHOT.md
```

---

### 🧪 НОВЫЕ ТЕСТЫ (без нового claim)

```
[ ] system_manifest.json → test_count обновить
[ ] reports/known_faults.yaml → # Last updated дата
[ ] README.md → badge + verification state count
[ ] AGENTS.md → Step 6 Verify count
[ ] llms.txt → How to verify + current state
[ ] index.html → все места (см. ниже)
[ ] CURSOR_MASTER_PROMPT_v2_X.md → acceptance commands

[ ] INDEX.HTML — 9 МЕСТ С ТЕСТАМИ:
    footer nav:        MIT · N tests · AUDIT PASS
    hero hv:           <span class="hv">N</span> tests
    hero badge:        <span class="hbproof-val cy">N</span>
    ticker ×2:         <span class="tn">N</span>
    stats counter:     <span id="cn2">N</span>
    psi-label:         N tests — CI passing
    osi-num:           <div class="osi-num">N</div>
    terminal:          N passed
    pricing:           N tests including adversarial proof
    JS counter:        ct(document.getElementById('cn2'),N,1500)

[ ] python scripts/deep_verify.py → ALL 10 PASSED

[ ] PROJECT KNOWLEDGE:
    [ ] EVOLUTION_LOG.md → CURRENT STATE tests count
    [ ] CLAUDE_PROJECT_MASTER → числа таблица
    [ ] AUDIT_PROTOCOL → ТЕКУЩЕЕ СОСТОЯНИЕ
```

**Grep перед коммитом:**
```powershell
Select-String "СТАРОЕ_ЧИСЛО" index.html, README.md, AGENTS.md, llms.txt, `
  system_manifest.json, CONTEXT_SNAPSHOT.md `
  | Where-Object {$_.Line -notmatch "rgba|#|color:|0,255"}
# Должен вернуть пустой результат
```

---

### 🌐 REAL DATA MODE (для нового claim)

```
[ ] backend/progress/<claim>.py → dataset_relpath параметр
[ ] backend/progress/data_integrity.py → fingerprint_file используется
[ ] tests/fixtures/<claim>_pass.csv — корректные данные
[ ] tests/fixtures/<claim>_fail.csv — данные с ошибкой
[ ] tests/<domain>/test_<claim>_realdata.py — тесты:
    - pass dataset → result.pass True
    - fail dataset → result.pass False
    - dataset fingerprint in inputs.dataset.sha256
    - different CSVs → different sha256
    - missing file → ValueError
    - no execution_trace in real data mode
[ ] tests/cli/test_real_data_e2e.py → добавить e2e тест для нового claim
[ ] docs/REAL_DATA_GUIDE.md → добавить CSV формат для нового claim

[ ] CURSOR_MASTER_PROMPT_v2_X.md → БЛОК L обновить (csv форматы)

[ ] PROJECT KNOWLEDGE:
    [ ] CLAUDE_PROJECT_MASTER → Real Data Mode таблица (✅ колонка)
    [ ] EVOLUTION_LOG → VERIFIED ARCHITECTURE
```

---

### 💰 ИЗМЕНЕНИЕ СПОСОБА ОПЛАТЫ

```
[ ] index.html → pricing секция + hero кнопки
[ ] COMMERCIAL.md → pricing таблица + payment methods
[ ] llms.txt → current state payment строка
[ ] CONTEXT_SNAPSHOT.md → payment строка
[ ] AGENTS.md → (если есть ссылка)
[ ] docs/REAL_DATA_GUIDE.md → pricing таблица
[ ] CURSOR_MASTER_PROMPT → БЛОК F payment строка

[ ] PROJECT KNOWLEDGE:
    [ ] CLAUDE_PROJECT_MASTER → ценообразование секция
    [ ] DECISION_LOG → DEC-XXX с объяснением почему
```

---

### 📣 ЗНАЧИТЕЛЬНЫЙ OUTREACH (≥5 писем)

```
[ ] CONTEXT_SNAPSHOT.md → outreach tracker таблица
[ ] llms.txt → outreach sent строка в current state
[ ] ppa/README_PPA.md → (если академик endorsement получен)

[ ] PROJECT KNOWLEDGE:
    [ ] EVOLUTION_LOG → outreach tracker полный
    [ ] CLAUDE_PROJECT_MASTER → outreach tracker секция
    [ ] NEXT_CHAT_PRIMER → если ждём ответов — в 🔴 раздел
```

---

### 🚀 НОВЫЙ ПУБЛИЧНЫЙ РЕЛИЗ (vX.Y.Z)

```
[ ] GitHub Release создан с тегом
[ ] README.md → Protocol badge обновлён
[ ] llms.txt → github_release строка
[ ] CONTEXT_SNAPSHOT.md → GitHub Release строка
[ ] system_manifest.json → version поле
[ ] index.html → если есть версия на сайте

[ ] PROJECT KNOWLEDGE:
    [ ] EVOLUTION_LOG → SESSION LOG строка
    [ ] CLAUDE_PROJECT_MASTER → ИСТОРИЯ таблица
```

---

### 🏗️ АРХИТЕКТУРНОЕ ИЗМЕНЕНИЕ

```
[ ] docs/PROTOCOL.md → обновить спецификацию
[ ] docs/ARCHITECTURE.md → обновить диаграммы
[ ] README.md → architecture section
[ ] llms.txt → What this repo does
[ ] AGENTS.md → Architecture in one paragraph
[ ] CONTEXT_SNAPSHOT.md → innovations / layers

[ ] PROJECT KNOWLEDGE:
    [ ] DECISION_LOG → DEC-XXX новое решение (ОБЯЗАТЕЛЬНО)
    [ ] EVOLUTION_LOG → VERIFIED ARCHITECTURE
    [ ] CLAUDE_PROJECT_MASTER → innovations + layers
```

---

## УРОК: КАК ПОЯВЛЯЮТСЯ ХВОСТЫ

| Когда | Что забыли | Последствие |
|-------|-----------|-------------|
| 2026-03-15 | 6 новых claims → не обновили все 12+ мест | Числа не совпадали везде |
| 2026-03-16 | Real data tests (+47) → манифест не обновлён | system_manifest.json отставал |
| 2026-03-16 | Real data tests → index.html не обновлён сразу | Пришлось отдельным PR |
| 2026-03-16 | JobStatus.value == "succeeded" | CI упал — case sensitivity |
| 2026-03-14 | Step Chain заявлен до проверки кода | Overclaim |

**Правило:** При добавлении тестов — **сразу** обновляй числа везде, в том же PR.
Не "потом пачкой" — именно в том же коммите.

---

## КОМАНДЫ ВЕРИФИКАЦИИ ПЕРЕД MERGE

```bash
# 1. Governance
python scripts/steward_audit.py
# → STEWARD AUDIT: PASS

# 2. Все тесты
python -m pytest tests/ -q
# → N passed

# 3. Полная верификация
python scripts/deep_verify.py
# → ALL 10 TESTS PASSED

# 4. Нет запрещённых слов
grep -r "tamper-proof\|GPT-5\|19x\|blockchain\|unforgeable" docs/ scripts/ backend/ tests/
# → пусто

# 5. Числа синхронны
Select-String "СТАРОЕ_ЧИСЛО" index.html, README.md, llms.txt, system_manifest.json
# → пусто
```

---

## PROJECT KNOWLEDGE — КАК ОБНОВЛЯТЬ

**Что обновлять и когда:**

| Файл | Обновлять когда |
|------|----------------|
| `EVOLUTION_LOG.md` | После каждой значительной сессии |
| `NEXT_CHAT_PRIMER.md` | При смене приоритетов |
| `CLAUDE_PROJECT_MASTER_vX.md` | При новых claims, числах, outreach |
| `AUDIT_PROTOCOL.md` | При новых уроках или новых местах для проверки |
| `DECISION_LOG.md` | При каждом нетривиальном архитектурном решении |
| `CURSOR_MASTER_PROMPT_v2_X.md` | При новых правилах, traps, real data |

**Процесс:**
```
1. Скачать файл из репо (или создать в Claude)
2. Обновить содержимое
3. Удалить старую версию из Project Knowledge
4. Загрузить новую версию
```

---

*UPDATE_PROTOCOL v1.0 — 2026-03-16 — MetaGenesis Core*
*Обновлять при появлении новых типов изменений*
