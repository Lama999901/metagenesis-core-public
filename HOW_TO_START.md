# Как запускать Claude Code + GSD

## ШАГ 1 — Открыть PowerShell
Win + X → Windows PowerShell

## ШАГ 2 — Запустить Claude Code
```
cd C:\Users\999ye\Downloads\metagenesis-core-public
claude
```

## ШАГ 3 — GSD команды (внутри claude >)
```
/gsd:quick "задача"      — быстрая задача
/gsd:plan-phase 9        — спланировать фазу
/gsd:execute-phase 9     — выполнить фазу
/gsd:progress            — посмотреть прогресс
/gsd:discuss-phase 9     — обсудить перед планом
```

## ПРОВЕРИТЬ СИСТЕМУ
```
python scripts/agent_evolution.py
```

## ЗАПУШИТЬ + PR
```
git push origin feat/gsd-phase-09-название
```
Потом GitHub → Pull Requests → Compare & pull request → merge

## ЕСЛИ КОНФЛИКТЫ
```
git checkout --ours ФАЙЛ.md
git add ФАЙЛ.md
git commit -m "fix: resolve conflict"
```
