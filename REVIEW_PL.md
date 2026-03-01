# Recenzja repozytorium `mods-supermarket`

Data przeglądu: 2026-03-01  
Zakres: szybki przegląd jakości kodu, uruchamialności testów i ryzyk utrzymaniowych.

## Najważniejsze obserwacje

### 1) Krytyczne: deklarowany backup save'a nie jest faktycznie wykonywany
W `AdvancedStatsModifier.modify_statistic` tworzona jest zmienna `backup`, ale plik kopii nie jest nigdzie zapisywany. Dodatkowo wykonywany jest „noop” (`p.write_text(p.read_text())`), który tylko przepisuje ten sam plik i nie daje realnego rollbacku.

**Wpływ:** modyfikacja save'a może nadpisać dane bez możliwości prostego odzyskania, mimo że UI/README sugerują mechanizmy bezpieczeństwa.

**Sugestia:** użyć `shutil.copy2(p, backup)` przed modyfikacją i logować ścieżkę backupu do `result`.

---

### 2) Wysokie: testy nie przechodzą na czystym środowisku
`pytest` kończy się błędami na etapie collect:
- `src/updater/test_import_updater.py` importuje `src.*` bez poprawnej konfiguracji ścieżki,
- brak zależności `psutil`, która jest importowana przez `advanced_lock.py`.

**Wpływ:** brak wiarygodnego sygnału CI/local quality gate; trudniej utrzymać regresje.

**Sugestia:**
- przenieść skrypt `src/updater/test_import_updater.py` poza konwencję testów (`scripts/` lub rename),
- dodać `psutil` do `requirements.txt` (albo uczynić import opcjonalnym z fallbackiem),
- rozważyć `pytest.ini` + `PYTHONPATH`/instalację pakietu w trybie editable.

---

### 3) Wysokie: ryzykowna semantyka wyszukiwania pól w save
Algorytm `_search_and_modify` dopasowuje pola po fragmencie nazwy (`if t.lower() in key_lower`) i modyfikuje **pierwsze** pasujące pole typu liczbowego.

**Wpływ:** łatwe przypadkowe nadpisanie nieintencjonalnego pola (false positive), szczególnie w złożonych strukturach JSON.

**Sugestia:**
- preferować dopasowanie exact-match + whitelist ścieżek,
- ewentualnie tryb „preview” pokazujący wszystkie kandydaty przed zapisem,
- uwzględnić obecnie nieużywane mapowanie `nested`.

---

### 4) Średnie: zależność od wewnętrznych metod lock managera
`GitHubUpdater` wywołuje metody prefiksowane `_` (`_read_lock_file`, `_is_process_alive`) z `AdvancedLockManager`.

**Wpływ:** silne sprzężenie i kruchość API; refaktoryzacja `AdvancedLockManager` może łatwo popsuć updater.

**Sugestia:** wystawić publiczne metody typu `read_lock()` / `is_lock_owned_by_live_process()`.

---

### 5) Średnie: monolityczna warstwa GUI
`src/gui/main_window.py` zawiera bardzo dużo odpowiedzialności w jednej klasie (UI, obsługa save, updater, polling, logika formularzy).

**Wpływ:** niższa testowalność i większe ryzyko regresji przy zmianach.

**Sugestia:** rozdzielić na mniejsze komponenty (np. `tabs/*`, `controllers/*`, `services/*`) i ograniczyć logikę biznesową w warstwie Tkinter.

---

## Co działa dobrze
- Projekt ma sensowny podział na moduły domenowe (`save_editor`, `save_detection`, `updater`, `gui`).
- Są obecne testy ukierunkowane na konkretne obszary (np. locki i modyfikator statystyk), co daje dobry fundament pod dalsze porządki.
- W updaterze widać świadomość problemów race condition i locków.

## Proponowana kolejność napraw
1. Naprawić realny backup i dopisać test regresyjny pod backup/restore.
2. Ustabilizować test suite (`psutil`, naming/pliki pomocnicze, konfiguracja importów).
3. Uszczelnić dopasowanie pól w `AdvancedStatsModifier` (exact paths + preview).
4. Odseparować publiczne API lock managera od metod prywatnych.
5. Iteracyjnie refaktoryzować `main_window.py` na mniejsze komponenty.
