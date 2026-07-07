# PokeLike Bot

PokeLike Bot is a free Windows automation tool for PokeLike. It provides a desktop GUI for opening one or many Chrome windows, starting PokeLike runs, automating reroll decisions, tracking run statistics, and prioritizing valuable Pokemon and item choices.

![PokeLike Bot desktop GUI](https://raw.githubusercontent.com/BIaze420/PokeLike-Bot/main/assets/pokelike-bot-screenshot.png)

## Main Features

- Desktop GUI with live status, runtime, run count, item rolls checked, encounters checked, target encounters, shinies seen, Pokegold, and Pokegold per hour.
- Full run automation for Challenge, Weekly, Daily, Battle Tower, and Story targets.
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

## Logic Highlights

- Shiny Pokemon are always prioritized when they appear.
- Legendary Pokemon and whitelist Pokemon are prioritized in full-run catch/reward decisions.
- Dragon and bug Pokemon are preferred before random fallback choices.
- Catch rerolls are only used after visible Pokemon choices are checked.
- Full-run mode counts shiny encounters from visible catch choices.
- Move Tutor / TM opportunities are prioritized for the main Pokemon until the move-upgrade quota is reached.
- Starting/passive item priority includes Shiny Hunter, Eject Pack, Soft Sand, Shiny Power, Stardust, Yache Berry, Grassy Seed, Dragon Scale, Light Clay, Power Bracer, Macho Brace, Black Belt, and Wise Glasses.
- Regular reward item priority includes Lucky Egg, Leftovers, Shell Bell, Dragon Fang, Rare Candy, and TM.

## Download

Download the latest Windows executable from the Releases page:

- `PokeLike Bot.exe`

If available, download the installer:

- `PokeLikeBotSetup.exe`

## First Run

On first launch, click `Open Browser` inside PokeLike Bot and log in to PokeLike in that bot-controlled browser window. The app uses its own local Selenium profile and does not ship personal Chrome cookies.

## Notes

This is an unofficial community automation tool for PokeLike. It is free to download and use. Use it responsibly and at your own risk.
