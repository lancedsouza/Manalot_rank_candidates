# Freeze inventory

- Base tag: `takeover-base` → cbf5808 (local; push with `git push origin takeover-base`).
- Working tree at freeze: clean except untracked `transition.md` (the framework — kept).
- Committed binaries containing personal data: `app/pdf/*.pdf` (4 candidate resumes), `app/jd_data/*.pdf`, plus Windows `:Zone.Identifier` files. **Owner decision needed:** keep, or remove from tree and history.
- Build loops / bots / deploy pipelines: none found in repo (no `.github/`). Owner to confirm nothing runs on Hugging Face Spaces / Streamlit Cloud (start.sh mentions port 7860 for HF).
