# Releasing ALPSbox

This checklist covers the steps that happen once, when the repository is first
published. The code, docs and metadata are already in publishable form; only the
final GitHub/Zenodo actions and the two identifiers below are missing.

## 1. Create the GitHub repository

1. Create an empty repository, e.g. `https://github.com/<owner>/alpsbox`.
2. Push the contents of this folder (the repository root is this folder):
   ```bash
   git init
   git add .
   git commit -m "ALPSbox v1.0.0"
   git branch -M main
   git remote add origin https://github.com/<owner>/alpsbox.git
   git push -u origin main
   ```

## 2. Fill the Zenodo DOI

The repository URL is already filled in `README.md`, `README.zh-CN.md`,
`docs/INSTALL.md`, `docs/zh-CN/INSTALL.md`, `CITATION.cff` and
`pyproject.toml`. After step 4 (Zenodo), fill the DOI with:

```bash
python scripts/fill_release_urls.py --doi 10.5281/zenodo.XXXXXXX
```

The script updates `CITATION.cff` (adds the DOI identifier), the `README`
files (DOI badge and a line in the "Citing ALPSbox" section) and
`docs/CITATIONS.md` (software citation). It is idempotent: it reports an
already-applied DOI instead of duplicating it. The same helper also supports
`--repo-url` if the repository is ever moved.

## 3. GitHub repository settings

- Description: "One-click DTI-ALPS processing with quality control and HTML
  reports (GUI/CLI, built on FSL)".
- Topics: `dti-alps`, `glymphatic`, `diffusion-mri`, `neuroimaging`, `fsl`,
  `quality-control`.
- Enable Issues; enable the "Cite this repository" button for `CITATION.cff`.
- The CI workflow in `.github/workflows/ci.yml` runs automatically on push/PR
  (byte-compile, release-integrity audit, TOPUP pairing tests and CLI smoke
  tests on Python 3.10–3.12).

## 4. Zenodo DOI

Zenodo can mint a DOI for a GitHub release:

1. Log in to <https://zenodo.org>, go to *Settings → GitHub* and enable the
   repository (do this **before** creating the release; Zenodo can only archive
   releases created after the switch is enabled).
2. Create a GitHub **release** with tag `v1.0.0` and title `ALPSbox v1.0.0`
   (the release tag must match the version in `pyproject.toml`,
   `CITATION.cff` and `CHANGELOG.md`).
3. Zenodo archives the release and displays the DOI. Fill it with the helper
   (step 2). `.zenodo.json` in the repository root supplies the metadata
   (title, description, keywords, licence, creators); edit it if you want to add
   named creators or ORCIDs.
4. Optionally add the DOI to the README (the helper does this) and cite it in
   `docs/CITATIONS.md` (the helper does this).

## 5. Optional: PyPI

The package is installable with `pip install -e .` from the repository. To
publish it on PyPI, install `build` and `twine`, then:

```bash
python -m build
python -m twine upload dist/*
```

Do this only after the source repository URL and DOI are final, because the
`pyproject.toml` URLs point at the GitHub repository (and the PyPI page will be
generated from this README).

## 6. Post-release checks

- `python tests/test_citations.py` passes locally and in CI.
- `alpsbox --version` prints `1.0.0`; `alpsbox --help` and
  `alpsbox --lang zh_CN --help` work.
- README screenshots render on GitHub (`docs/assets/screenshots/`).
- The example report opens: `docs/example_report.html`.
- `CITATION.cff` validates (e.g. GitHub "Cite this repository" preview, or
  `cffconvert --validate` if installed).
