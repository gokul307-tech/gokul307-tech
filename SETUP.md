# Setup

1. Create a **public** GitHub repository named exactly `gokul307-tech`.
2. Extract this ZIP and open the folder in VS Code.
3. The portrait SVG and dashboard artwork are generated assets. The original portrait is in `local-assets/` and excluded from Git to keep the photograph private.
4. In PowerShell, from this folder:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   python scripts/make_ascii_svg.py
   python scripts/fetch_contributions.py
   python scripts/render_heatmap_svg.py
   python scripts/make_dashboard.py
   ```

5. Commit and push all files to the `gokul307-tech` repository.
6. On GitHub, open **Actions**, enable workflows if asked, then run **Update GitHub profile art** once. The workflow refreshes the contribution graph, developer statistics, dashboard SVG, and GIF fallback.
7. Your profile README appears when the repository is public and named exactly after your username.

The workflow refreshes public GitHub statistics and the contribution graph daily at 01:17 UTC (06:47 IST). It does not require a personal access token. Since the portrait source is intentionally excluded from Git, Actions normally skips portrait regeneration and uses the committed `avi-ascii.svg`; it never uploads or requires the original photograph. To regenerate the portrait locally, run `python scripts/make_ascii_svg.py` while the private source is present. Never add your GitHub password or token to this project.
