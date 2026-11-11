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

## 2. Fill the repository URL and (later) the Zenodo DOI

Two placeholders exist: `https://github.com/your-org/alpsbox` (in `README.md`,
`README.zh-CN.md`, `docs/INSTALL.md`, `docs/zh-CN/INSTALL.md`, `CITATION.cff`,
`pyproject.toml`).

Use the helper once the real URL (and, after step 4, the DOI) are known:

```bash
python scripts/fill_release_urls.py \
    --repo-url https://github.com/<owner>/alpsbox \
    --doi 10.5281/zenodo.XXXXXXX
```

Run it with `--repo-url` only after step 1; run it again with `--doi` after step
4. The script updates the URLs, `CITATION.cff` (adds the DOI identifier), the
`README` files (DOI badge and a line in the "Citing ALPSbox" section) and
`docs/CITATIONS.md` (software citation). It refuses to run when the replacement
would be a no-op or when the same DOI is already present.

## 3. GitHub repository settings

- Description: "One-click DTI-ALPS processing with quality control and HTML
  reports (GUI/CLI, built on FSL)".
- Topics: `dti-alps`, `glymphatic`, `diffusion-mri`, `neuroimaging`, `fsl`,
  `quality-control`.
- Enable Issues; enable the "Cite this repository" button for `CITATION.cff`.
- The CI workflow in `.github/workflows/ci.yml` runs automatically on push/PR
  (byte-compile, release-integrity audit, CLI smoke tests on Python 3.9–3.12).

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
