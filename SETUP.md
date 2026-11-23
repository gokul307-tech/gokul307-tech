# Setup

1. Create a **public** GitHub repository named exactly `gokul307-tech`.
2. Extract this ZIP and open the folder in VS Code.
3. The portrait SVG is already generated. The original portrait is in `local-assets/` and excluded from Git.
4. In PowerShell, from this folder:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   python scripts/make_ascii_svg.py
   ```

5. Commit and push all files to the `gokul307-tech` repository.
6. On GitHub, open **Actions**, enable workflows if asked, then run **Update GitHub profile art** once.
7. Your profile README appears when the repository is public and named exactly after your username.

The workflow refreshes the public contribution graph daily at 01:17 UTC (06:47 IST). It does not require a personal access token. The portrait source is not committed. Never add your GitHub password or token to this project.
