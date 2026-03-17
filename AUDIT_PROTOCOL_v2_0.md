# MetaGenesis Core — Audit Protocol
> Версия 2.0 — 2026-03-15
> Читать при каждом изменении проекта. Живой документ — пополняется после каждого нового хвоста.

---

## ПРИНЦИП: PROOF NOT TRUST

Применяется ко мне (Claude) так же как к коду.
Не говорю "всё готово" — показываю код который это докажет.
Не говорю "я запомнил" — показываю команду которая это подтвердит.

**Главная команда верификации:**
```bash
python scripts/deep_verify.py
# → ALL 10 TESTS PASSED
```
Если не ALL 10 — не говорю "готово". Сначала чиним.

---

## ТРИ УРОВНЯ ПРОВЕРКИ ПЕРЕД КАЖДЫМ КОММИТОМ

### Уровень 1 — числа
При смене числа тестов — grep по всем файлам:
```powershell
Select-String "СТАРОЕ_ЧИСЛО" `
  index.html, README.md, llms.txt, CONTEXT_SNAPSHOT.md, `
  system_manifest.json, ppa\README_PPA.md, reports\known_faults.yaml, `
  docs\ROADMAP.md, ppa\CLAIMS_DRAFT_v2.md, docs\ARCHITECTURE.md, `
  AGENTS.md, CONTRIBUTING.md `
  | Where-Object {$_.Line -notmatch "rgba|255,140"}
# Пустой результат = хвостов нет
```

**Альтернатива — Python скрипт (надёжнее):**
```python
# Запустить final_sweep.py (в .gitignore — только локально)
python final_sweep.py
```

### Уровень 2 — архитектурные слова
При добавлении новой фичи — grep по словам которые её описывают:
```powershell
# Добавили новый claim → ищем старое число:
Select-String "13 claim|13 active" index.html, README.md, llms.txt, CONTEXT_SNAPSHOT.md

# Добавили verification layer → ищем старое число:
Select-String "two.*verif|2.*layer" index.html, README.md, llms.txt

# Добавили инновацию → ищем старое число:
Select-String "4 patent|4 innov" index.html, README.md, ppa\README_PPA.md
```

### Уровень 3 — логическая согласованность
Перед тем как сказать "готово" — три вопроса:
1. **Заявление в тексте/комментарии → есть ли это в коде?**
2. **Число в UI → совпадает ли с реальностью?**
3. **Новая фича → обновлены ли ВСЕ места где она упоминается?**

---

## ТАБЛИЦА: ФИЧА → ЧТО ГРЕПАТЬ

| Добавили | Что грепать | Файлы |
|----------|-------------|-------|
| Новые тесты | старое число | index.html (11+ мест), README, llms.txt, CONTEXT_SNAPSHOT, system_manifest, known_faults, ROADMAP, CLAIMS_DRAFT_v2, ppa/README_PPA, ARCHITECTURE, AGENTS, CONTRIBUTING |
| Новый claim | `"13 claim"`, `"13 active"` | везде |
| Новый verification layer | `"two"`, `"2.*layer"` | index.html, README, llms.txt |
| Новую инновацию | `"4 patent"`, `"4 innov"` | index.html, README, ppa/README_PPA |
| Новый домен | `"6 domain"` | index.html, README, llms.txt |
| MVP v0.X | `"MVP v0.X"` | все .py файлы в backend/, scripts/, tests/ |

---

## КАРТА МЕСТ В index.html

При смене числа тестов — 11 мест:
| # | Что искать |
|---|-----------|
| 1 | `<span class="hbproof-val cy">N</span>` — hero badge |
| 2 | `<span class="hv">N</span> tests` — hero meta |
| 3-4 | `<span class="tn">N</span><span class="tl">Tests Passing</span>` — ticker ×2 |
| 5 | `<span id="cn2">N</span>` — stats counter |
| 6 | `std` описание tests |
| 7 | `ct(document.getElementById('cn2'),N,1500)` — JS анимация |
| 8 | `N passed in 2.70s` — demo terminal |
| 9 | `N passing tests` — founder story |
| 10 | `MIT · N tests · AUDIT PASS` — site map |
| 11 | `N tests including adversarial proof` — pricing |

При смене числа claims — 3+ места:
| # | Что искать |
|---|-----------|
| 1 | `<span class="hbproof-val ok">N</span>` — hero badge |
| 2 | `<span class="hv">N</span> active claims` — hero meta |
| 3 | `<span id="cn1">N</span>` — stats counter |
| 4 | `ct(document.getElementById('cn1'),N,...)` — JS |

---

## ПРАВИЛО: ПЕРЕД ПУБЛИЧНЫМ ПОСТОМ / HN / OUTREACH

Любое техническое заявление → проверяю в коде:
```
Заявление: "three independent verification layers"
→ читаю scripts/mg.py _verify_semantic()
→ убеждаюсь что все три слоя реально проверяются
→ только потом пишу
```

Если заявление опережает код — сначала допиливаю код, потом постим.

---

## ПРАВИЛО: deep_verify ПЕРЕД КАЖДЫМ MERGE

```bash
python scripts/deep_verify.py  # → ALL 10 TESTS PASSED
```

Что проверяет:
1. steward_audit PASS — 14 claims, bidirectional, phase 42
2. 223 tests GREEN — реальный pytest
3. 14/14 JOB_KIND в runner — каждый dispatch
4. 14/14 Step Chain — chain=True
5. Cross-Claim Chain — anchor_hash меняет downstream hash
6. Нет forbidden terms в коде
7. Сайт 14/223/3/7 == system_manifest
8. Demo end-to-end PASS PASS
9. Bypass attack CAUGHT — Layer 2 semantic
10. verify-chain в CLI

---

## ТЕКУЩЕЕ СОСТОЯНИЕ (обновлять при каждом изменении)

```
Claims:              14
Tests:               223
Verification layers: 3 (integrity + semantic + step chain)
locked_paths:        3
Patentable innov:    5 (+ Cross-Claim Chain)
Domains:             7
deep_verify:         ALL 10 TESTS PASSED
```

---

## KNOWN LESSONS (пополняется)

| Дата | Урок | Как поймали |
|------|------|-------------|
| 2026-03-14 | Числа в 12+ местах, не в 3 | PowerShell Select-String |
| 2026-03-14 | git push на неправильную ветку | `git branch` перед push |
| 2026-03-14 | Remote ahead → rejected | `git stash → pull --no-rebase → pop → push` |
| 2026-03-14 | Step Chain заявлен но не верифицируется в mg.py | читал код перед публикацией |
| 2026-03-14 | Verification layers = 2 на сайте после добавления 3го | наблюдательность Yehor |
| 2026-03-15 | MVP v0.1 в 22 .py файлах не обновлён | Python batch replace скрипт |
| 2026-03-15 | Windows cp1252 не печатает emoji в subprocess | io.TextIOWrapper encoding=utf-8 |
| 2026-03-15 | deep_verify проверяет сам себя на forbidden terms | `if f.name == "deep_verify.py": continue` |
| 2026-03-15 | reports/ledger_snapshots/ не в .gitignore | добавлен в .gitignore |
| 2026-03-15 | FUNDING.yml не в policy gate allowlist | добавлен в allow_globs |
| 2026-03-15 | AGENTS.md таблица claims не обновлена (8→14) | grep "8 claim" в всех doc файлах |
| 2026-03-15 | CLAIMS_DRAFT_v2 имел только 3 из 9 post-filing claims | читал файл полностью перед выводом |
| 2026-03-16 | JobStatus.value == 'SUCCEEDED' → CI upал | не status.value == 'succeeded' — только == JobStatus.SUCCEEDED |
| 2026-03-16 | origin section 223→270 не обновился | grep ALL включая prose-текст, не только UI-теги |
| 2026-03-16 | test count update в отдельном PR | числа обновлять В ТОМ ЖЕ PR что добавляет тесты |
| 2026-03-16 | real data tests +47: manifest/docs не обновлены | UPDATE_PROTOCOL.md — см. чеклист "🧪 НОВЫЕ ТЕСТЫ" |

---

## ПРОТОКОЛ ПРИ СЛЕДУЮЩЕМ ИЗМЕНЕНИИ

```
1. Понять ЧТО меняется (число / архит. слово / новая фича)
2. Составить список файлов где это упоминается
3. Запустить: python final_sweep.py (или Select-String) ДО коммита
4. Проверить логическую согласованность (Уровень 3)
5. Убедиться что код соответствует заявлению
6. python scripts/deep_verify.py → ALL 10 TESTS PASSED
7. Только потом коммитить и постить
```

---

*AUDIT_PROTOCOL v2.1 — 2026-03-16 — MetaGenesis Core*
*Следующее обновление: при обнаружении нового типа хвоста или нового правила*
