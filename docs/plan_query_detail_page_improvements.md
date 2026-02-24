# Plan: Query Detail Page Improvements

## 1. Charts verbessern

### 1a. Chart-Engine Fixes & Features (`frontend/js/detail.js`)
- [ ] **Sortierung erhalten** — Bar-Charts: Reihenfolge aus SQL-Daten beibehalten (`new Set()` verliert Sortierung)
- [ ] **Achsenlabels** — x/y-Achsenbeschriftungen aus viz-Config anzeigen (aktuell fehlen sie komplett)
- [ ] **Tooltip-Formatierung** — Zahlen mit Tausendertrennzeichen in Tooltips
- [ ] **DataZoom für Zeitreihen** — Scroll-/Zoom-Bar unter dem Chart für line/bar mit vielen Datenpunkten
- [ ] **PNG Export** — ECharts built-in `saveAsImage` Toolbox aktivieren
- [ ] **Chart-Titel** — Optional aus Query-Metadaten

### 1b. Fehlende Visualisierungen ergänzen (`queries_bq.py`)
- [ ] **Q04** (IPC classes) → horizontal bar chart (`ipc_class` × `assignment_count`)
- [ ] **Q07** (green tech trends) → grouped line chart (`appln_filing_year` × `applications`, color: `ctry_code`)
- [ ] Systematisch alle 47 Queries durchgehen und `visualization: null` prüfen
- [ ] Wo sinnvoll: Charts ergänzen, `export_queries.py` re-run → `queries.json` aktualisieren

## 2. Parameter Controls verbessern

### 2a. Year Range Slider (`buildYearRange`)
- [ ] **Editierbare Zahlenfelder** neben den Slidern (statt nur Anzeige-Spans)
- [ ] **Validation** — `year_start ≤ year_end` erzwingen (Slider koppeln)
- [ ] **Dynamische Bounds** — min/max aus Query-Defaults ableiten statt hardcoded 1782–2024

### 2b. Multiselect (`buildMultiselect`)
- [ ] **Select All / Deselect All** Buttons
- [ ] **Counter** — "3 of 9 selected" Anzeige

### 2c. Run Button
- [ ] **Doppelklick-Schutz** verbessern (visuelles Feedback nach Erfolg/Fehler)

## 3. Results Table verbessern

- [ ] **CSV Export Button** für Query-Ergebnisse
- [ ] **Zahlenformatierung** — Dezimalstellen konsistent, große Zahlen mit Separator, Zahlen rechts ausgerichtet
- [ ] **Truncation-Warnung** — Deutlicherer Hinweis wenn >200 Rows abgeschnitten werden

## Vorgeschlagene Reihenfolge

| Prio | Schritt | Aufwand |
|------|---------|---------|
| 1 | 1a: Chart-Engine (Sortierung, Labels, Tooltips, DataZoom, Export) | mittel |
| 2 | 1b: Fehlende Visualisierungen in queries_bq.py | mittel |
| 3 | 2a: Year-Range mit Zahlenfeldern + Validation | klein |
| 4 | 2b: Multiselect Select All / Deselect All + Counter | klein |
| 5 | 3: CSV Export + Zahlenformatierung | klein |
| 6 | 2c: Run-Button Feedback | klein |
