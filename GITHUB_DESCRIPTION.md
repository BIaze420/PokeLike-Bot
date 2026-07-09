<p align="center">
  <img src="https://raw.githubusercontent.com/BIaze420/PokeLike-Bot/main/assets/readme-banner.png" alt="PokeLike Bot - star and watch the repository" width="100%">
</p>

<h1 align="center">PokeLike Bot</h1>

<p align="center">
  <a href="https://github.com/BIaze420/PokeLike-Bot/releases/latest">
    <img src="https://img.shields.io/badge/Download_latest_EXE-21c16b?style=for-the-badge&logo=windows&logoColor=white" alt="Download latest EXE">
  </a>
  <a href="https://github.com/BIaze420/PokeLike-Bot/stargazers">
    <img src="https://img.shields.io/github/stars/BIaze420/PokeLike-Bot?style=for-the-badge&label=Star%20this%20project&color=ffd24a" alt="Star this project on GitHub">
  </a>
  <a href="https://github.com/BIaze420/PokeLike-Bot/subscription">
    <img src="https://img.shields.io/badge/Watch_for_updates-65d9ff?style=for-the-badge&logo=github&logoColor=111827" alt="Watch this repository for updates">
  </a>
</p>

PokeLike Bot is a free Windows automation tool for PokeLike. It provides a desktop GUI for opening one or many Chrome windows, starting PokeLike runs, automating reroll decisions, tracking run statistics, and prioritizing valuable Pokemon and item choices.

If this bot helps you, please give the repository a star and watch it for updates. It supports the project and helps the maintainer's GitHub account grow.

## Download

Download the latest Windows executable from the Releases page:

- `PokeLike Bot.exe`

![PokeLike Bot desktop GUI](https://raw.githubusercontent.com/BIaze420/PokeLike-Bot/main/assets/readme-main-gui.png)

## Main Features

- Desktop GUI with live status, runtime, run count, item rolls checked, encounters checked, target encounters, shinies seen, Pokegold, and Pokegold per hour.
- Full run automation for Challenge, Weekly, Daily, Battle Tower, and Story targets.
- Task schedule for chaining daily, weekly, and repeated achievement runs.
- Shiny Charm reroll mode.
- Shiny Pokemon reroll mode.
- Normal Pokemon reroll mode.
- Configurable starter and Pokemon whitelist.
- Multi-browser launch with automatic window tiling.
- Starting/passive item priority editor.
- Regular reward item priority editor.
- Starting/passive item ignore list.
- Unknown starting item tracking for improving priority lists.
- Full-run catch logic that prioritizes shiny Pokemon, legendary Pokemon, whitelist Pokemon, dragon types, bug types, then fallback choices.
- Catch-reroll logic that checks visible Pokemon before rerolling.
- Shiny encounter counting during full runs.
- Rare Candy automation for the first Pokemon.
- Move tutor / TM handling for the main Pokemon.
- Reward and replacement policies for shiny, legendary, and priority Pokemon.
- Play Again / retry handling on end screens.
- Branded Lunatic Labs header and Windows app icon.

## Task Schedule

The task schedule can run multiple goals in order, such as Daily Challenge until one win, Weekly Challenge until one win, then Story Classic - Kanto for a chosen number of runs. Each task has a run target, an advance condition (`Wins` or `Runs`), and an amount.

![Task schedule window](https://raw.githubusercontent.com/BIaze420/PokeLike-Bot/main/assets/readme-task-schedule.png)

## Logic Highlights

- Shiny Pokemon are always prioritized when they appear.
- Legendary Pokemon and whitelist Pokemon are prioritized in full-run catch/reward decisions.
- Dragon and bug Pokemon are preferred before random fallback choices.
- Catch rerolls are only used after visible Pokemon choices are checked.
- Full-run mode counts shiny encounters from visible catch choices.
- Move Tutor / TM opportunities are prioritized for the main Pokemon until the move-upgrade quota is reached.
- Starting/passive item priority includes Shiny Hunter, Eject Pack, Soft Sand, Shiny Power, Stardust, Yache Berry, Grassy Seed, Dragon Scale, Light Clay, Power Bracer, Macho Brace, Black Belt, and Wise Glasses.
- Regular reward item priority includes Lucky Egg, Leftovers, Shell Bell, Dragon Fang, Rare Candy, and TM.

## First Run

On first launch, click `Open Browser` inside PokeLike Bot and log in to PokeLike in that bot-controlled browser window. The app uses its own local Selenium profile and does not ship personal Chrome cookies.

## Notes

This is an unofficial community automation tool for PokeLike. It is free to download and use. Use it responsibly and at your own risk.
