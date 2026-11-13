"""Wires the signal intake into a GardenState each frame and updates every Controllable with it."""

import logging

from controllables import (
    Controllable,
    ControllableState,
    GardenState,
    LookingGlassControllable,
    ShowMode,
)
from branches import BranchController, BranchDriver
from config import OSCConfig, TreehouseConfig
from garden_state import SignalIntake

log = logging.getLogger("treehouse")


def build_controllables(
    config: TreehouseConfig, branch_driver: BranchDriver | None = None,
) -> list[Controllable]:
    """The Controllables the Pi drives itself. The LED locations are ESP32-S3
    controllers reached through LocationSender (ADR-0020), not Controllables.
    Without a *branch_driver* the branches get an unconnected one, which drops commands."""
    if branch_driver is None:
        branch_driver = BranchDriver(config.branch.port, config.branch.baud)
    return [
        LookingGlassControllable(config.looking_glass),
        BranchController(config.branch, branch_driver),
    ]


class Coordinator:
    """Owns all Controllable instances, drives the frame loop, manages show state."""

    def __init__(
        self,
        controllables: list[Controllable],
        intake: SignalIntake | None = None,
        dim_level: float = 0.25,
    ) -> None:
        self._controllables: dict[str, Controllable] = {c.name: c for c in controllables}
        self._looking_glass: LookingGlassControllable | None = next(
            (c for c in controllables if isinstance(c, LookingGlassControllable)), None
        )
        self.intake = intake or SignalIntake(OSCConfig().heartbeat_interval_s)
        self.mode = ShowMode.ACTIVE
        self._dim_level = dim_level
        self._last_state = GardenState()

    @property
    def garden_state(self) -> GardenState:
        """The GardenState the most recent update() ran on."""
        return self._last_state

    @property
    def brightness(self) -> float:
        if self.mode == ShowMode.INACTIVE:
            return 0.0
        if self.mode == ShowMode.DIM:
            return self._dim_level
        return 1.0

    def set_mode(self, mode_str: str) -> None:
        try:
            self.mode = ShowMode(mode_str)
            log.info("Show mode → %s (brightness %.2f)", self.mode.value, self.brightness)
        except ValueError:
            log.warning("Unknown show mode %r; valid: %s", mode_str, [m.value for m in ShowMode])

    def set_dim_level(self, level: float) -> None:
        self._dim_level = max(0.0, min(1.0, level))
        log.info("Dim level → %.2f", self._dim_level)

    def set_looking_glass_scene(self, scene: str) -> None:
        if self._looking_glass:
            self._looking_glass.set_scene(scene)

    def update(self, dt: float) -> None:
        state = self.intake.snapshot(self.mode, self.brightness)
        # Held for LocationSender, which reads it after update() returns and
        # needs to see the one-shot blowup flag this frame was built with.
        self._last_state = state
        for controllable in self._controllables.values():
            controllable.update(dt, state)

    def get_all_states(self) -> list[ControllableState]:
        return [c.get_state() for c in self._controllables.values()]

    @property
    def controllable_names(self) -> list[str]:
        return list(self._controllables.keys())
