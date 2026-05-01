# All FundingCAPTCHA games must self-terminate on inactivity

Every FundingCAPTCHA game type must guarantee a loss if Players stop interacting — either through a literal countdown timer, or through mechanics that ensure failure without input (e.g. defenders eventually catching the ball carrier in Keepaway).

## Consequences

The Screensaver only needs to watch for inactivity in the between-game state. There is no mid-Arc idle interrupt, no "pause" state, and no special handling for Players walking away mid-game. A game that can run forever without input would require a separate timeout mechanism to recover and would leave the kiosk stuck in a dead state.

All future game implementations must satisfy this constraint before being added to the rotation.
