# OTS W.H.I.T.E. desktop design

## Intent

A dark slate / steel-blue desktop security workspace. The inspiration was a
high-fidelity clipboard application; **only its visual language is reused**.
OTS W.H.I.T.E. remains a repository-auditing application, not a clipboard
recorder. No clipboard contents are read or stored.

## Palette

| Token | Color |
|---|---|
| Canvas | \`#0F172A\` |
| Surface | \`#1E293B\` |
| Main steel-blue accent | \`#34587C\` |
| Deep slate-blue | \`#24405E\` |
| Electric dusty blue | \`#4E79A7\` |
| Icy highlight | \`#8BA8CD\` |
| Main text | \`#FFFFFF\` |

## Working desktop features

- Native Tkinter sidebar, repository selection, audit controls, status banner,
  finding counts, and live searchable audit findings.
- Category chips filter **Secrets**, **SAST**, and **Dependencies**, preserving
  the existing scanner's result types and report formats.
- Findings appear in dense, vertically scrolling dark-surface cards; severity,
  rule, location, and privacy-safe explanation are visible.
- Selecting a card displays the corresponding remediation recommendation.
- More results are loaded in batches so very large scans do not immediately
  create thousands of GUI controls.
- The Windows executable embeds the ICO; the PNG appears in the desktop header
  and window icon, and ships as Python package data.

## Limits

Tkinter provides no native backdrop blur, fractional-alpha borders, or
cross-platform rounded-window corners. Its dark cards, hairline solid borders,
highlight states, and careful spacing approximate the desired glassmorphism.
The optimized 128px PNG is intentionally sized for desktop UI use. Original
source artwork can be maintained separately for print/high-resolution media.

All scan logic remains local and unchanged. Missing OSV-Scanner or offline
advisory databases continue to produce incomplete SCA outcomes; a theme
change does not change the scanner's security guarantees.
