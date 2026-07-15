## PokeLike Bot v1.0.6

- Enlarged the default main window so all controls and the shop roll log are visible without manual resizing.
- Added a compact shop roll log to the main window for recent shop reroll results.
- Shows the current Legendary Egg shiny rate from the Poke Mart text.
- Hardened Legendary shop reroll force-upload flow after a hit: click revealed egg sprite, close shop, open either full-size or compact menu, click Cloud Sync, click Force Upload, and accept Chrome confirmation.
- Kept failed shop attempt browsers isolated so one bad prewarm browser closes and the reroll continues.
- Updated release docs from Shiny Charm reroll to Item reroll and fixed a passive item description typo.
- Added schedule support for Legendary shop reroll until gold is below the next egg price, then continuing into the next scheduled task.
- Added `Forever` schedule tasks for infinite Challenge Mode farming, including saved starter/settings snapshots such as Darkrai.
- Added shop-mode stats for last shiny rolled and uploaded targets obtained, while excluding post-hit safety-run shinies from shop shiny totals.
- Shop reroll Chrome windows now match the bot window size.
- Guarded automated cloud uploads so normal Full run mode cannot trigger the shop upload path.
