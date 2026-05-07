from dataclasses import dataclass, field
from enum import StrEnum


class Mode(StrEnum):
    DURAS_TRIALS = "Dura's Trials"
    AFK_STAGES = "AFK Stages"
    SEASON_AFK_STAGES = "Season AFK Stages"
    LEGEND_TRIALS = "Season Legend Trial"

    def is_duras(self) -> bool:
        return self in {Mode.DURAS_TRIALS}

    def is_afk_stages(self) -> bool:
        return self in {Mode.AFK_STAGES, Mode.SEASON_AFK_STAGES}

    def has_timer(self) -> bool:
        """Added in case there is ever a battle mode without a timer."""
        return self in {
            Mode.AFK_STAGES,
            Mode.SEASON_AFK_STAGES,
            Mode.LEGEND_TRIALS,
            Mode.DURAS_TRIALS,
        }


@dataclass
class BattleState:
    mode: Mode | None = None
    max_attempts_reached: bool = False
    formation_num: int = 0
    faction: str | None = None
    is_manual_battle: bool = False
    manual_active_heroes: list = field(default_factory=list)
    manual_hero_positions: dict = field(default_factory=dict)

    @property
    def section_header(self) -> str | None:
        if not self.mode:
            return None
        if self.mode == Mode.LEGEND_TRIALS:
            if not self.faction:
                return "Legend Trial"
            return f"Legend Trial - {self.faction} Tower"
        return self.mode.value

    @property
    def faction_lower(self) -> str | None:
        if self.faction:
            return self.faction.lower()
        return None
