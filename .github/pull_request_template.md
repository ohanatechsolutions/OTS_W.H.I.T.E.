## Summary

Explain the change and why it is needed.

## Areas affected
- [ ] Core scanner / redaction
- [ ] Offline OSV adapter
- [ ] GUI / Windows packaging
- [ ] CI / GitHub configuration
- [ ] Documentation only

## Verification
- [ ] `python -m unittest discover -s tests -v`
- [ ] `python -m ots_white . --no-sca --format table`
- [ ] Other checks (describe):

Record actual commands, exit codes and any skipped checks rather than claiming unrun tests passed.

## Security and privacy
- Does any source, secret candidate, file path or dependency inventory leave the local machine?
- Does this change report fields, logging, new dependencies or release packaging?
- Does it preserve fail-closed behavior for incomplete scans?

## Notes
Do not paste live credentials, private target code or raw private scan reports into PRs.
