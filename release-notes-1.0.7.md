PokeLike Bot v1.0.7

- Fixed full-run catch filtering so non-matching catch screens flee/skip instead of resetting the run, while the optional start-shiny gate still rerolls the run when it misses.
- Improved Pokemon type detection from visible type badges and removed the team-type scan that could crash with `detectedTypesFor is not defined`.
- Added smart trait-aware catch selection using the visible trait panel, including Bug 4/4 vs shiny Bug 6/6 target math.
- Added default held-item, combat-item, passive priority, and never-pick lists based on the current sorted item pool.
- Simplified combat item setup: mark combat items directly in the held priority list; boss swaps use that order.
- Prevented item rewards from selecting lower-priority held or combat items when a better one is already owned.
- Added usable held-item handling for whitelisted pickup items such as Rare Candy, TM, and Sacred Ash.
- Improved challenge-run resume/home handling and startup shiny-filter rerolls.
- Flattened the main log area and made the item priority editor smoother with a single selection toolbar.
