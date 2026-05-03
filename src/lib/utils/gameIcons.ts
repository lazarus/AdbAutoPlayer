// Per-game accent color and short label used as a visual identifier
// (e.g. in the running task hero). Falls back to deriving initials from
// the game title for unknown games.

interface GameIcon {
  initials: string;
  color: string;
  image?: string;
}

const gameMap: Record<string, GameIcon> = {
  "AFK Journey": {
    initials: "AJ",
    color: "#a78bfa",
    image: "/AFKJourney/icon.ico",
  },
};

export function getGameIcon(gameTitle: string | undefined | null): GameIcon {
  if (!gameTitle) return { initials: "?", color: "var(--accent)" };
  const exact = gameMap[gameTitle];
  if (exact) return exact;

  const words = gameTitle.split(/\s+/).filter(Boolean);
  const initials =
    words.length > 1
      ? words
          .slice(0, 2)
          .map((w) => w[0])
          .join("")
          .toUpperCase()
      : gameTitle.slice(0, 2).toUpperCase();
  return { initials, color: "var(--accent)" };
}
