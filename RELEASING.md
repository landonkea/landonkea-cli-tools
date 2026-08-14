# Releasing

Five stdlib-only scripts, no `pip install`, nothing built or published to a registry. "Release" here just means: a git tag that marks what a specific version of these tools looked like, plus a GitHub Release page with notes. Two channels, `dev` and `main`, and two tag formats to match.

## Branches

- **`dev`**: where changes land first. CI (`ci.yml`) runs on every push here same as anywhere else, but nothing on `dev` is a promise, it's the pre-release channel.
- **`main`**: stable. Only things that have been tagged as an RC and looked good get merged in from `dev`. Every commit on `main` should be safe to tag.

## Tags

- **`vX.Y.Z-rcN`**, a release candidate. Tag the tip of `dev` (or any commit you want a broader test on) once it's ready to be checked before going stable. `v1.3.0-rc1`, then `v1.3.0-rc2` if that first candidate needed a fix, and so on.
- **`vX.Y.Z`**, a stable release. Only accepted on a commit reachable from `main`. The release workflow checks this itself and fails the run instead of publishing if the tag points somewhere else, so tagging a feature branch by mistake can't produce a stable release.

Bump `Z` for bug fixes, `Y` when a tool gains a new flag or mode, `X` when something changes an existing script's arguments or output in a way that would break someone's existing command line or a script parsing the output. Nothing enforces this split automatically right now, it's a convention until `--version` support (see FEATURE_IDEAS.md #22) gives each tool something real to report.

## Cutting a release candidate

```bash
git checkout dev
git pull
git tag v1.3.0-rc1
git push origin v1.3.0-rc1
```

The pushed tag triggers `.github/workflows/release-candidate.yml`: ruff, then the test suite, then a GitHub Release marked as a pre-release with auto-generated notes. A lint or test failure stops the release before anything gets published.

## Cutting a stable release

```bash
git checkout main
git merge dev
git push origin main
git tag v1.3.0
git push origin v1.3.0
```

The pushed tag triggers `.github/workflows/release.yml`. It checks that the tagged commit is actually reachable from `main` first (a tag pushed anywhere else fails the run before ruff or the tests even run), then applies the same lint/test gate as the RC workflow, then publishes a GitHub Release with notes generated from everything committed since the last tag.

## Why not a version file

A `_version.py` or similar makes sense once one of these tools needs to report its own version at runtime, that's FEATURE_IDEAS.md #22, currently unbuilt. Until then, the tag itself is the version record, and the GitHub Release page is the changelog. If that changes, the tagging convention here doesn't need to, only the publish step would gain a step that also bumps a file in the repo.
