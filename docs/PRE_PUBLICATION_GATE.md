# Public Repository Release Gate — 2026-11-01

**Status: HOLD. Do not change repository visibility until all required gates pass.**
Maintainer: Ohana Tech Solutions and ICF-AI.

## Scope

- ohanatechsolutions/OTS_System_Santizer
- ohanatechsolutions/OTS_W.H.I.T.E.
- ohanatechsolutions/OTS_Clipboard_History
- ohanatechsolutions/OTS_Firewall79X
- ohanatechsolutions/AI-Development-Prompts
- ICF-AI/ICF_AI_HQ
- ICF-AI/AI_Efficiency_Toolkit
- ICF-AI/ICF_Chrome_Extension

## Completed initial checks

- The current readable main-branch text was checked using secret-signature, suspicious assignment, URL-credential and personal-contact patterns. No confirmed live credential was found. Detector fixture strings and example addresses were identified.
- File inventories for the main branches and all 32 additional OTS Firewall79X branch tips were examined; a current-file inventory is **not** a full Git history secret scan.
- Representative historical commits and one recent Actions job log per active repository were checked. This is **not** exhaustive log or history inspection.
- Standardized secret-file exclusions were added to every repository's .gitignore. These do not remove historical data.
- MIT licenses now cover original author-owned code across all eight repositories. Third-party assets retain their own licenses and attribution requirements.
- OTS System Sanitizer pull-request checks were separated from its privileged installer publishing workflow.
- OTS Firewall79X no longer automatically publishes new large Git LFS installer versions on routine commits. Release assets replace routine LFS distribution.

## Blocking gates — complete BEFORE making anything public

1. **Scan full Git history locally, across all branches and tags.** Clone each repo using the signed-in GitHub CLI or Git Credential Manager; do not place access tokens in URLs, chat, logs or command lines. Use full clones (not GitHub source ZIPs). Fetch all remote refs and tags.
2. From a trusted local installation of OTS W.H.I.T.E., run
   `py -3 -m ots_white "C:\\path\\to\\cloned-repo" --history --no-sca --fail-on medium --format table --output "C:\\private-audit-reports\\repo-name.txt"`
   on **each** clone. This is a heuristic offline history scan, *not* a guarantee that every secret is detectable. Treat exit status 2 / incomplete results as a hard failure; investigate findings and accepted false positives.
3. Independently corroborate with a reputable current secret scanner such as Gitleaks or TruffleHog configured for full Git history. Avoid publishing raw secret values in logs or issues. Do not upload private source to external scanning services without explicit consideration of the data transfer.
4. Inspect ALL historical revisions containing suspicious paths, all archived branch tips, public-facing issue/PR discussions, old Actions logs and downloadable release assets. GitHub's visibility change exposes existing Actions history/logs. Existing binary installers and preview release archives have not been independently decoded and inspected through this GitHub connection.
5. If any real secret is discovered: **revoke/rotate the credential FIRST**. Then plan history cleanup with collaborators, delete/recreate contaminated releases/artifacts as appropriate, and scan the cleaned repository again. A normal deletion commit does not purge Git history.
6. Inspect EXE, ZIP, SBOM, manifest and provenance artifacts for embedded private endpoints, identifiers, credentials or sensitive debug data. Verify checksum/PE provenance and scan binaries locally. Do not infer executable safety merely from a matching SHA-256.
7. In GitHub repository Settings, protect `main`: block force pushes/deletion, require passing checks, require PRs for outsiders, and apply a reasonable review process that does not lock out a solo maintainer. GitHub's linked app does not currently expose writing repository rulesets or changing visibility.
8. In GitHub Billing, configure and **verify** $0 hard-stop spending budgets for Actions, Actions storage, Git LFS storage and bandwidth, and other enabled metered products. Set the policy for EACH account (ohanatechsolutions and ICF-AI). A new budget does not retroactively erase earlier usage.
9. Set the desired public commit email behavior; historical commits with real addresses may still expose those addresses. Do not rewrite authorship history solely for cosmetics without planning references and releases.
10. Audit third-party assets and maintain copyright/attribution notices: ICF_AI_HQ includes Microsoft Rocketbox MIT and some CC BY assets whose credit requirements persist.
11. Explicitly check GitHub `Settings > Security & analysis` after public conversion for free secret scanning and private vulnerability reporting. Do not enable paid code-security products without reviewing billing.

## Distribution policy

Keep original source in Git, not ever-growing installer binaries.
- Deliver Windows installers and matching SHA-256 files as **GitHub Release assets**.
- OTS Firewall79X releases are currently development previews, **not complete or production-certified security products**.
- Existing historical Git LFS objects can continue accruing storage use; removing today's pointer does not erase earlier LFS storage. A full cleanup requires separate billing and history review.

## Publication decision record

- [ ] All eight full-history scans completed, independent scanner corroboration recorded
- [ ] No live credential / private information exposures remain or every exposure is revoked and accepted
- [ ] Binaries and release assets examined
- [ ] Third-party notice obligations verified
- [ ] Branch protections enabled and tested
- [ ] $0 account billing hard stops verified
- [ ] Public email/metadata exposure accepted
- [ ] Maintainer confirms a repository-specific publication checklist

**Current decision: NOT APPROVED FOR PUBLICATION.** Lack of a confirmed finding is not the same as a complete negative audit.


## Executable audit runner added November 1, 2026

A read-only audit runner is included at scripts/publication_gate.py. It uses a private temporary working directory and never modifies remote GitHub repositories. It requires Python 3.11+, Git, GitHub CLI authenticated to an account authorized for each repository, and Gitleaks 8.19+, installed from trusted vendor releases. Use existing CLI authentication; do not enter credentials into a script, URL or support ticket.

Run from a trusted checkout of OTS W.H.I.T.E.:

~~~powershell
py -3 -m unittest discover -s tests -v
py -3 scripts/publication_gate.py --output "$env:USERPROFILE\Documents\ots-private-publication-audit.json"
~~~

The audit enumerates all eight named repositories; it pulls complete remote branches, tags, and accessible pull-request heads; runs full-history Gitleaks plus OTS W.H.I.T.E.'s local history scanner; downloads existing release assets; and scans common ASCII/UTF-16LE credential shapes in these files and ZIP members. It leaves raw scanner reports in a temporary directory that is deleted. The written JSON contains counts and file names but never actual detected secret strings.

For account-specific authentication, use the GitHub CLI commands gh auth status, gh auth login, and gh auth switch, authenticating to an account that can read each private repository. Re-run failed repositories individually with the --repo owner/name option. The script fails closed when scanners, history, or release inspection cannot complete. Its publication_cleared field is always false by design: no script can attest malware freedom, legal permission, or account billing limits.

Important binary limitations: historical executable/ZIP blobs require independent provenance and malware review. Git LFS pointers do not include the original binary bytes; the script does not download them because doing so can consume billable LFS bandwidth. Older GitHub Actions logs, caches, discussion attachments, and binary file formats such as RAR/7z also require separate review. A clean output cannot replace these publication gates.

## Cost and repository administration

GitHub standard hosted runners are free for public repositories; larger runners, Git LFS, and some storage remain metered. Before changing visibility, visit the owner account Billing > Budgets and alerts controls for BOTH ohanatechsolutions and ICF-AI. Set $0 product budgets for metered Actions/storage and LFS usage, select Stop usage when budget limit is reached wherever available, confirm each budget is a hard stop rather than an email-only alert, and enable included-usage alerts. A newly created budget does not erase earlier consumption in the same cycle.

The connected GitHub app cannot modify account billing, repo visibility, branch-protection settings, or inspect all private binary bytes. Those controls must be confirmed in GitHub settings before publication. For public repos, configure branch rulesets that prohibit deletion/force pushes, require appropriate review, and disallow modification of trusted release workflows without owner approval.


## Interim no-automatic-private-runner-cost guard

As part of the November 1, 2026 preparation, the automatically triggered jobs in all seven workflow-bearing repositories were updated with a repository-visibility guard. They skip GitHub-hosted runner execution while the repository is private. Automated checks resume when the repository becomes public. Manual workflow_dispatch invocations remain possible in private repositories and can still consume included usage or create costs. Five installer-heavy workflow artifact retentions were also reduced from seven days to one day; this does not delete existing stored artifacts or erase past usage.

This guard protects **new automatic runner compute**, but is not a GitHub billing hard stop. Previously stored artifacts, Git LFS history, manual runs, and other metered products still require the account-level budget settings above. After converting any repository to public, verify that its critical workflow checks actually run, are green, and are included in required branch rules. Do not claim tests passed when they were skipped by the private-repository cost guard.


## Additional GitHub-side checks — November 1, 2026

- **AI Development Prompts:** full inventory of five preexisting distinct Git blobs across its original five commits reviewed for common credential signatures, embedded-credential URLs, and email-address patterns. No matches in those blobs. A public-facing README has since been added. Historical commit author metadata includes a non-noreply email address.
- **ICF Chrome Extension:** ten commits and their readable file patches checked for common credential signatures, private-key markers and embedded-credential URLs; no matches. Historical image binaries are not text-scannable. All four existing Actions job logs were retrieved and screened for credential patterns and email-address strings; no matches. Historical commit author metadata includes a non-noreply business-domain email.
- **OTS Firewall79X:** fifteen GitHub Releases contain 193 attachments totaling approximately 3.56 GB. Release-note and attachment-name pattern checks found no credentials; the actual executable, ZIP and image bytes **were not** inspected. Release assets remain a publication blocker until independently scanned.
- The read-only publication scanner in scripts/publication_gate.py was hardened to import the bundled OTS W.H.I.T.E. code correctly when launched as a script and to bound total decompressed ZIP content. Its local syntax and five behavioral checks passed. This does not count as running the scanner on private Git clones.
- All eight repositories remain private. Billing budgets, visibility changes and main branch protection are account-level actions outside the connected repository-file operations. Do not publish on the basis of these checks alone.

**Publication decision remains HOLD for all repositories until historical checks, binary inspection where applicable, and owner account billing limits are verified.** Git author addresses and older workflow logs may be exposed on publication; the user must review and accept that exposure, or plan appropriate mitigation before changing visibility.


## Billing clarification — November 1, 2026

The owner reports gross metered usage of $0.14 and an equal included-usage discount of $0.14 for November, so the reported net usage is $0.00. The owner does not wish to add a payment method. Do not add one solely for a spending budget: GitHub generally blocks excess paid Actions usage when no valid payment method is on file. Existing guidance elsewhere in this document about setting $0 budgets is conditional on an account having a payment method or an active paid product. Review BOTH personal-account billing pages for net charges and any paid products before publishing. Public repositories can use standard GitHub-hosted runner minutes for free; Git LFS and certain storage/runner services may have separate limits. These observations are not verification of actual payment method status in either account.
