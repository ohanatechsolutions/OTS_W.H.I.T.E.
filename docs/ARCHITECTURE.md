# Aegis White architecture and security boundaries

## Dataflow

```
local checkout / fetched Git refs
     |  read-only, bounded file traversal (no symlinks)
     +--> secret rules + entropy/assignment heuristics ----+
     +--> scoped SAST/config rules ------------------------+--> findings (no secret bytes)
     +--> git rev-list/cat-file (optional, all local refs) -+
     +--> OSV-Scanner v2 --offline (optional executable) ---+
                                                           |
                                              JSON / table / SARIF
                                                           |
                                        local report / optional CI gate
```

## Trust model

- Scan only repositories you own or are explicitly authorized to audit.
- Untrusted repository files are treated as untrusted **data**, never imported or executed.
- Git history is read via Git plumbing (`rev-list`, `cat-file`) and never checked out into an executable worktree.
- Credential material is detected but never retained in findings. Do not add `--debug` dumps of source text.
- SCA invokes only a trusted, separately installed OSV-Scanner v2 in full `--offline --no-resolve` mode. Prepare/update the DB **outside** audited projects.
- The CLI does **not** transmit repository content, telemetry, credentials, or dependency lists. Network activity is not part of this CLI. CI in GitHub runs on GitHub infrastructure and is therefore not equivalent to local execution.
- All output stays local unless users explicitly upload SARIF or share logs. SARIF includes path, line, and advisory metadata; treat reports as sensitive.

## Limitations and threat model

- This is an initial ruleset with **heuristic** secrets/SAST detections, not a sound proof of security; it produces both false positives and false negatives.
- The regex SAST module is not a dataflow or taint analyzer and cannot reliably detect reachable exploitation or complex injection paths.
- The history scanner covers all **locally available** Git objects reachable from local refs; use a full clone/fetch for complete remote history. It does not cover GitHub's inaccessible detached objects, fork histories, inaccessible branches, or remote PR heads not fetched locally.
- `--base` analyzes changed paths at current checkout; deleted file secrets require `--history`.
- Most SCA ecosystems need lockfiles; `requirements.txt` may be unpinned and insufficient for accurate vulnerability matching; use `pip freeze`/lockfile or SBOM and verify OSV support.
- OSV offline mode has known extraction/coverage limitations. Database freshness is the user's responsibility; absence of matches does not prove dependencies safe.
- Minimum secret length, file caps, binary skips, exclusions, and inline suppressions can all cause misses. Oversized/unreadable files become operational errors (exit 2) rather than silent success.
- Filesystem paths and malicious untrusted filenames may appear in reports; review before external sharing.

## Rule development

- Add scoped patterns in `sast.py`, or targeted signatures in `secrets.py`.
- Always supply a failing test before changing pattern semantics.
- Never add raw matches, source snippets, request headers, tokens, or environment variables to report fields.
- Any new network integration must be explicitly opt-in and document exactly which data leave the machine.

## Exit codes

- `0` requested modules complete and below severity threshold.
- `1` scan complete with finding at or above `--fail-on` threshold.
- `2` incomplete/operational problem (e.g., scanner missing, missing local database, unreadable file, Git failure).
