---
name: figma-make
description: >
  Automates Figma Make to generate AI design drafts via browser automation.
  ONLY trigger this skill when the user explicitly mentions "Figma Make", "FigmaMake",
  "figma make", or "figmamake" — do NOT trigger for generic design requests.
  Examples: "用 FigmaMake 生成设计稿", "help me use Figma Make to create a homepage",
  "用figmamake做一个登录页". Do NOT trigger for: "帮我设计一个页面", "create a design",
  or other requests that don't explicitly name Figma Make.
---

# Figma Make 自动化设计生成

This skill automates Figma Make via browser (Playwright) to generate AI design drafts. The script handles browser launch, Figma login session, prompt input, and waits for generation to complete.

## Setup (run once before first use)

Before executing the script for the first time, verify the environment:

1. **Check Python (3.10+)**
   ```bash
   python --version
   # or on Mac/Linux:
   python3 --version
   ```
   If missing, download from https://python.org

2. **Check Playwright**
   ```bash
   python -c "import playwright; print('OK')"
   ```
   If missing or error:
   ```bash
   pip install playwright
   playwright install chromium
   ```

3. **Check Figma session**
   Look for `figma-session.json` next to the script. If it doesn't exist, the first run will open a browser window — log in to Figma manually and the session will be saved automatically for future runs.

4. **Check Figma Make access**
   Your Figma account must have FigmaMake enabled. If the script can't find the Make button, your account or region may not have access yet.

**When helping a user run this skill for the first time, always run through these checks before executing the script. If any check fails, help the user fix it before proceeding.**

---

## Script location

`scripts/figma-make.py` within the skill directory.

The key variable is `DESIGN_PROMPT` near the top of the script — this is what gets sent to Figma Make as the design requirement.

## Execution steps

### 1. Handle the design requirement

**If the user provided a design description:**
- Translate it to English if needed (Figma Make works best with English prompts)
- Edit `figma-make.py` — replace the entire `DESIGN_PROMPT` string (lines 23–41) with a well-structured English prompt based on the user's request. Include: theme/style, color palette, typography, layout sections, and visual details.
- Confirm the edit with the user before running.

**If no design description was provided:**
- Use the existing `DESIGN_PROMPT` in the script (WoW-style game website — dark fantasy theme).

### 2. Run the script

**Windows:**
```bash
python scripts/figma-make.py
```

**Mac / Linux:**
```bash
python3 scripts/figma-make.py
```

The script runs in headed (visible) browser mode. It will:
- Load the saved Figma session from `figma-session.json` (auto login)
- Navigate to Figma drafts
- Click the Make button
- Type the design prompt
- Submit and wait for AI generation (up to 5 minutes)
- Print the generated Figma file URL

### 3. Return the result

Once the script outputs a URL, share it with the user:
- Figma file URL (e.g. `https://www.figma.com/make/...`)
- Note that screenshots are saved to `screenshots/` for debugging if needed

## Troubleshooting

- **Login required**: If `figma-session.json` doesn't exist or is expired, the script will pause and ask the user to log in manually in the browser window. After login, it saves the session automatically.
- **Make button not found**: Check `screenshots/01_figma_home.png` to see current page state. The script uses multi-strategy selectors — if Figma's UI changed, the selectors in `find_and_click_make_button()` may need updating.
- **Generation timeout**: Script waits up to 5 minutes. If it times out, check `screenshots/05_timeout.png` and the Figma drafts page manually.
