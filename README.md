# PokeLike Bot

PokeLike Bot is a free Windows automation tool for [PokeLike](https://pokelike.xyz/). It opens one or more Chrome browser windows, starts configured PokeLike runs, and automates common reroll and full-run decisions from a desktop GUI.

The bot is built with Python, CustomTkinter, Selenium, and webdriver-manager. It is intended for users who want a simple downloadable tool, and for developers who want to inspect or modify the automation logic.

## Features

- **Graphical control panel** with run status, runtime, run count, item rolls checked, encounters checked, target encounters, shinies seen, Pokegold, and Pokegold per hour.
- **Multiple run modes**:
  - Full run
  - Shiny Charm reroll
  - Shiny Pokemon reroll
  - Normal Pokemon reroll
- **Run target selection** for Challenge Mode, Weekly Challenge, Daily Challenge, Battle Tower regions, and Story regions.
- **Starter selection** with a configurable starter field.
- **Pokemon whitelist** used by Pokemon reroll modes and full-run catch priority.
- **Multi-browser support** with configurable browser count.
- **Parallel browser launch** so several Chrome windows can open faster.
- **One-load browser startup**: each browser opens PokeLike once, then the app tiles the windows.
- **Window tiling** for multi-browser sessions.
- **Optional manual-start flow** that can use the current run screen on the first attempt.
- **Item priority editor** for starting/passive items and regular reward items.
- **Full-run item automation** with separate starting/passive item priority and regular reward priority.
- **Starting-item ignore list** for items that should never be picked at the passive/starting item screen.
- **Unknown starting item tracking** to help improve the item priority list over time.
- **Catch priority logic** for full runs:
  - Prioritizes shiny Pokemon.
  - Prioritizes legendary Pokemon.
  - Prioritizes Pokemon from the whitelist.
  - Prioritizes dragon and bug choices before random fallback.
  - Uses catch rerolls only after checking the currently visible Pokemon choices.
- **Shiny encounter counting in full-run mode** using visible catch choices encountered during the run.
- **Rare Candy automation** that clicks the Rare Candy badge and uses it on the first Pokemon when available.
- **Move tutor / TM handling** with a quota for the main Pokemon in full-run mode.
- **Team replacement policy** for shiny, legendary, and priority Pokemon rewards.
- **End-screen handling** for Play Again / retry flows.
- **Live money tracking** with Pokegold per hour.
- **Branded Lunatic Labs header** with bundled logo assets and Windows icon.

## Requirements

For source runs:

- Windows 10 or newer
- Python 3.11 recommended
- Google Chrome
- Internet access on first run so webdriver-manager can download the matching ChromeDriver

For normal users, the packaged `.exe` is the easiest option.

## Download

Go to the GitHub Releases page for this repository and download the latest Windows build:

- `PokeLike Bot.exe`

If an installer is provided, download:

- `PokeLikeBotSetup.exe`

## First Run Login

PokeLike Bot uses its own Selenium Chrome profile. It does not use or ship your normal Chrome cookies.

The first time you run the bot:

1. Open PokeLike Bot.
2. Click `Open Browser`.
3. Log in to PokeLike inside the browser window opened by the bot.
4. Complete any cookie/consent prompts if they appear.
5. After you are logged in, choose your mode/settings in the bot and click `Start Bot`.

The packaged app stores its own login/session data locally under:

```text
%LOCALAPPDATA%\PokeLike Bot\selenium-profile
```

That folder is created on the user's computer after running the app. It is not included in this repository or in the release source code.

## Running From Source

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

## Building The EXE

From PowerShell:

```powershell
.\build_exe.ps1
```

The executable will be created at:

```text
dist\PokeLike Bot.exe
```

## Building The Installer

1. Build the executable first:

```powershell
.\build_exe.ps1
```

2. Install [Inno Setup](https://jrsoftware.org/isinfo.php).
3. Open `installer.iss` in Inno Setup Compiler.
4. Compile it.

The installer output will be created in:

```text
PokeLikeBotInstaller\PokeLikeBotSetup.exe
```

## Data Storage

When running from source, settings are stored next to `main.py`.

When running as a packaged `.exe`, user data is stored under:

```text
%LOCALAPPDATA%\PokeLike Bot
```

That folder contains user settings, the Selenium Chrome profile, and unknown starting item tracking.

## GitHub Release Build

This repository includes a GitHub Actions workflow:

```text
.github/workflows/build-windows.yml
```

It builds the Windows executable when:

- You manually run the workflow.
- You push a version tag like `v1.0.0`.

## Disclaimer

This is an unofficial community automation tool for PokeLike. Use it responsibly and at your own risk. PokeLike Bot is not affiliated with PokeLike.
