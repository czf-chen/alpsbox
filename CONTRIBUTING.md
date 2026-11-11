# Contributing

Thanks for your interest in ALPSbox. This project is a thin, reproducible
front-end around FSL/MRtrix3 for the DTI-ALPS index; contributions that keep the
tool focused (per-subject ALPS + quality control) are welcome.

## Ways to contribute

- **Bug reports / feature requests**: open an issue with the command you ran,
  the full error message, the OS/WSL version, FSL and Python versions, and (if
  relevant) the output folder structure. Do not upload subject data.
- **Translations / wording**: user-facing text is bilingual (English and
  Simplified Chinese) in `alpsbox/i18n.py` and the `alpsbox/text_*.py`
  catalogs. Keep both languages in sync, keep units and placeholders unchanged,
  and do not add claims that are not supported by the cited literature.
- **Documentation**: `README.md` (English), `README.zh-CN.md` (Chinese) and
  `docs/` must stay structurally aligned.
- **Code**: by default every change must keep the shipped processing definition
  unchanged. If a change alters processing (defaults, registration route, ROI
  definition), it changes the measurement: document it, record the affected
  results, and update `docs/VALIDATION.md` and `CHANGELOG.md`.

## Development setup

```bash
git clone https://github.com/your-org/alpsbox.git
cd alpsbox
python -m pip install -e .
python tests/test_citations.py          # release/citation audit, no FSL needed
```

Processing requires FSL (and optionally MRtrix3): see
[docs/INSTALL.md](docs/INSTALL.md). The GUI additionally needs `tkinter`
(`python3-tk` on Linux). Tests that run the real pipeline require FSL and are
not part of the default test suite.

## Project conventions

- **No "official" claims**: ALPS has no official/standard implementation. Use
  "reference implementation" only for `gbarisano/alps` (MIT) with its commit and
  companion paper; see `docs/CITATIONS.md`. The audit in
  `tests/test_citations.py` enforces this.
- **Citations**: every method, tool and data source used by the pipeline is
  listed in `alpsbox/citations.py` / `docs/CITATIONS.md`. Add a formal citation
  (authors, title, journal, year;volume(issue):pages, DOI) when you introduce a
  new method or third-party tool.
- **Outputs are part of the contract**: `alps_summary.csv`, `alps_result.json`
  and `qc_report.txt` are consumed by downstream statistics. Do not rename
  fields; add new ones instead.
- **English-first**: code comments, docstrings and documentation are written in
  English; user-facing text is provided in both English and Chinese.
- **No patient data in the repository**: demo data must stay synthetic.

## Licence

By contributing you agree that your contributions are licensed under the MIT
License (see `LICENSE`). Bundled ROI masks are reproduced from
`gbarisano/alps` under its MIT licence (see `LICENSE_Barisano_alps.txt` and
`alpsbox/data/ROIs_JHU_ALPS/PROVENANCE.md`).
