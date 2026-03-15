# MetaGenesis Core — Audit Protocol
> Версия 1.0 — 2026-03-14
> Читать при каждом изменении проекта. Живой документ — пополняется после каждого нового хвоста.

---

## ПРИНЦИП: PROOF NOT TRUST

Применяется ко мне (Claude) так же как к коду.
Не говорю "всё готово" — показываю grep который это докажет.
Не говорю "я запомнил" — показываю протокол который это обеспечит.

---

## ТРИ УРОВНЯ ПРОВЕРКИ ПЕРЕД КАЖДЫМ КОММИТОМ

### Уровень 1 — числа
При смене числа тестов — grep по всем файлам:
```powershell
Select-String "СТАРОЕ_ЧИСЛО" `
  index.html, README.md, llms.txt, CONTEXT_SNAPSHOT.md, `
  system_manifest.json, ppa\README_PPA.md, reports\known_faults.yaml, `
  docs\ROADMAP.md, ppa\CLAIMS_DRAFT_v2.md `
  | Where-Object {$_.Line -notmatch "rgba|255,140"}
# Пустой результат = хвостов нет
```

### Уровень 2 — архитектурные слова
При добавлении новой фичи — grep по словам которые её описывают:
```powershell
# Добавили verification layer → ищем старое число слоёв:
Select-String "two.*verif|2.*layer|Verification Layers|cn3" `
  index.html, README.md, llms.txt, CONTEXT_SNAPSHOT.md

# Добавили новый claim → ищем старое число claims:
Select-String "7 claim|7 active|7 domain" `
  index.html, README.md, llms.txt, CONTEXT_SNAPSHOT.md

# Добавили новую инновацию → ищем старое число:
Select-String "4 patent|4 innov" `
  index.html, README.md, ppa\README_PPA.md
```

### Уровень 3 — логическая согласованность
Перед тем как сказать "готово" — три вопроса:
1. **Заявление в тексте/комментарии → есть ли это в коде?**
   *(урок 2026-03-14: Step Chain заявлен как третий слой → mg.py его не проверял)*
2. **Число в UI → совпадает ли с реальностью?**
   *(урок 2026-03-14: добавили 3й слой → сайт показывал 2)*
3. **Новая фича → обновлены ли ВСЕ места где она упоминается?**
   *(урок 2026-03-14: 6 мест в index.html + README оставались с "two")*

---

## ТАБЛИЦА: ФИЧА → ЧТО ГРЕПАТЬ

| Добавили | Что грепать | Файлы |
|----------|-------------|-------|
| Новые тесты | старое число (напр. `113`) | index.html (9 мест), README, llms.txt, CONTEXT_SNAPSHOT, system_manifest, known_faults, ROADMAP, CLAIMS_DRAFT_v2, ppa/README_PPA |
| Новый claim | `"7 claim"`, `"7 active"` | везде |
| Новый verification layer | `"two"`, `"2.*layer"`, `"Verification Layers"`, `cn3` | index.html, README, llms.txt |
| Новую инновацию | `"4 patent"`, `"4 innov"` | index.html, README, ppa/README_PPA |
| Новый домен | `"5 domain"`, `"6 domain"` | index.html, README, llms.txt |
| Новый verification layer | `integrity.*semantic`, `semantic.*layer`, `two layer`, demo steps JS, phys-check блок, FAQ | index.html полный grep |
| Новое заявление в тексте | читаю реальный код который это реализует | scripts/mg.py, tests/ |

---

## ПРАВИЛО: ПЕРЕД HN / ПУБЛИЧНЫМ ПОСТОМ

Любое техническое заявление → проверяю в коде:
```
Заявление: "three independent verification layers"
→ читаю scripts/mg.py _verify_semantic()
→ убеждаюсь что все три слоя там реально проверяются
→ только потом пишу комментарий
```

Если заявление опережает код — сначала допиливаю код, потом постим.

---

## МЕСТА В index.html (актуальная карта)

При смене числа тестов — 9 мест:
| # | Что искать |
|---|-----------|
| 1 | `<span class="hbproof-val cy">N</span>` — hero badge |
| 2 | `<span class="hv">N</span> tests` — hero meta |
| 3 | `<span class="tn">N</span><span class="tl">Tests Passing</span>` — ticker копия 1 |
| 4 | то же — ticker копия 2 |
| 5 | `<span id="cn2">N</span>` — stats counter |
| 6 | `std` описание tests — текст |
| 7 | `ct(document.getElementById('cn2'),N,1500)` — JS анимация |
| 8 | `N passed in 2.70s` — demo terminal |
| 9 | `N passing tests` — founder story |
| 10 | `MIT · N tests · AUDIT PASS` — site map |
| 11 | `N tests including adversarial proof` — pricing |

При смене числа verification layers — 6 мест:
| # | Что искать |
|---|-----------|
| 1 | `<span class="tn">N</span><span class="tl">Verification Layers</span>` — ticker копия 1 |
| 2 | то же — ticker копия 2 |
| 3 | `<span id="cn3">N</span>` — stats counter |
| 4 | `ct(document.getElementById('cn3'),N,900)` — JS анимация |
| 5 | `two/three independent verification layers` — pitch section |
| 6 | `two/three independent verification layers` — how it works |

---

## ТЕКУЩЕЕ СОСТОЯНИЕ (обновлять при каждом изменении)

```
Claims:              8
Tests:               118
Verification layers: 3 (integrity + semantic + step chain)
locked_paths:        3
Patentable innov:    4 (+ step_chain_verification как 5й в system_manifest)
Domains:             6
```

---

## KNOWN LESSONS (пополняется)

| Дата | Урок | Как поймали |
|------|------|-------------|
| 2026-03-14 | Числа в 12+ местах, не в 3 | PowerShell Select-String |
| 2026-03-14 | git push на неправильную ветку | `git branch` перед push |
| 2026-03-14 | Remote ahead → rejected | `git stash → pull --rebase → pop → push` |
| 2026-03-14 | Step Chain заявлен но не верифицируется в mg.py | читал код перед публикацией |
| 2026-03-14 | Verification layers = 2 на сайте после добавления 3го | наблюдательность Yehor |
| 2026-03-14 | Step Chain не упомянут в Live Verifier demo, phys-check PASS блоке, FAQ | полный grep после фичи |

---

## ПРОТОКОЛ ПРИ СЛЕДУЮЩЕМ ИЗМЕНЕНИИ

```
1. Понять ЧТО меняется (число / архит. слово / новая фича)
2. Составить список файлов где это упоминается
3. Select-String по всем ДО коммита
4. Проверить логическую согласованность (Уровень 3)
5. Убедиться что код соответствует заявлению
6. Только потом коммитить и постить
```

---

*AUDIT_PROTOCOL v1.0 — 2026-03-14 — MetaGenesis Core*
*Следующее обновление: при обнаружении нового типа хвоста*
