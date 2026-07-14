## PokeLike Bot v1.0.5

- Added separate Shiny Pokemon shop reroll and Legendary shop reroll modes.
- Legendary shop reroll buys the 10,000 Pokedollar legendary egg; shiny shop reroll buys the 2,000 Pokedollar shiny egg.
- Added isolated disposable Chrome attempt profiles so failed shop rolls can be discarded without uploading save data.
- Added cloud-upload guards for shop reroll attempts; only a confirmed hit is force-uploaded.
- Added faster shop reroll prewarming while keeping save profiles isolated.
- Added shop ignore list support as a reverse whitelist.
- Improved egg result detection using sprite class, shiny sprite path, sparkle marker, name, and Dex fallback.
- Fixed force-upload flow after a shiny hit: dismisses the egg reveal, opens account menu, clicks Force Upload, accepts the Chrome confirmation, closes the menu, and keeps the winning Chrome window open.
- Fixed a prewarm race where upload could target the wrong Chrome driver.
- Fixed alert handling for Chrome's force-upload confirmation.
- Skipped live profile backup copying for winning profiles because Chrome locks those files while the final window stays open.
