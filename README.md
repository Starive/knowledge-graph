# Equilibrium Prototype Knowledge Graph

An editable version of the knowledge graph from RGC proposal 27628327, *Form-Finding Based on Equilibrium Prototypes*. It is drawn in the notation of the proposal's Figure 3:

- **Arch-cable** is the core prototype, and **Triangular Arch** and **Triangular Cable** are the original prototypes that combine into it.
- Eight adjusted prototypes open into **32 In-Between States**.
- Each In-Between State is materialised as one representative **built case**. All 78 collected cases are included, either as the representative or as an alternate that can be swapped in.

**Open it:** `https://starive.github.io/knowledge-graph/`. The address works once GitHub Pages is switched on for this repository.

## What's here

| Path | What it is |
|---|---|
| `index.html` | The graph editor: drag circles, change links and commands, swap cases, export PNG, SVG or JSON |
| `photos/sources.json` | Where each case's photo comes from: the Miro board's chosen Commons file, or a Commons search |
| `scripts/fetch_photos.py` | Downloads the photos (run by GitHub Actions) |
| `photos/manifest.json` | Written by the script; the editor reads it to fill the photo rings |
| `CREDITS.md` | Author, licence and source page of every photo |

## Reviewing the graph

- Click any circle or link to see its details.
- Photos picked by *Wikimedia Commons search* in `CREDITS.md` were chosen automatically, so check them before use.
- To change a photo, edit its entry in `photos/sources.json` (a Commons file name or a search). The **Fetch case photos** action then runs again.
- Edits made in the browser stay in that browser. Use **Export → JSON** to share a changed layout.
