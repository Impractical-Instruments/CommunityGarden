import logging
from dataclasses import dataclass

from .base import Controllable, ControllableState, GardenState

log = logging.getLogger("treehouse")


@dataclass
class LookingGlassConfig:
    name: str = "Looking Glass"
    scene: str = "bloom"
    speed: float = 1.0
    # Number of virtual mirror reflections rendered by the video engine
    mirror_depth: int = 6


class LookingGlassDisplay(Controllable):
    """
    Generative video inside a physical mirrored box ('Looking Glass' garage window).

    The mirrored enclosure multiplies every rendered frame into an infinite-
    regression tunnel. The video engine receives scene parameters each frame
    via the control interface below.

    Scenes
    ------
    bloom     – slow organic growth spirals
    fractal   – recursive geometric growth
    mycelium  – branching network propagation
    cosmos    – stellar nebula drift
    """

    SCENES = ("bloom", "fractal", "mycelium", "cosmos")

    def __init__(self, config: LookingGlassConfig) -> None:
        super().__init__(config.name)
        self.scene = config.scene
        self.speed = config.speed
        self.mirror_depth = config.mirror_depth
        self._time = 0.0

    # ------------------------------------------------------------------
    # Control interface
    # ------------------------------------------------------------------

    def set_scene(self, scene: str) -> None:
        if scene not in self.SCENES:
            raise ValueError(f"Unknown scene {scene!r}; choices: {self.SCENES}")
        log.info("Looking Glass scene → %s", scene)
        self.scene = scene

    def set_speed(self, speed: float) -> None:
        self.speed = max(0.0, speed)

    def set_mirror_depth(self, depth: int) -> None:
        self.mirror_depth = max(1, depth)

    # ------------------------------------------------------------------
    # Display lifecycle
    # ------------------------------------------------------------------

    def update(self, dt: float, state: GardenState) -> None:
        if not self.enabled:
            return
        self._time += dt * self.speed
        # TODO: push {scene, time, mirror_depth} to video renderer each frame
        # (e.g. via OSC, shared-memory texture, or socket to a TouchDesigner patch)

    def get_state(self) -> ControllableState:
        return ControllableState(
            name=self.name,
            enabled=self.enabled,
            params={
                "scene": self.scene,
                "speed": self.speed,
                "mirror_depth": self.mirror_depth,
                "time": round(self._time, 2),
            },
        )
