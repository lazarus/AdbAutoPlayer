// Inline SVG paths and accent colors for known task labels.
// Keys are lowercase substrings matched against the task label.
// Falls back to a generic icon when no match is found.
//
// IMPORTANT: order matters. Earlier entries win, so list more-specific
// keywords (e.g. "season afk stages") before less-specific ones ("stages").

interface TaskIcon {
  path: string;
  color: string;
}

const iconMap: Array<{ keywords: string[]; icon: TaskIcon }> = [
  // ===== Game Modes (specific keywords first) =====
  {
    // Season AFK Stages → chess-rook (castle tower)
    keywords: ["season afk stages", "season afk"],
    icon: {
      color: "#a78bfa",
      path: "M5 21h14V11H5v10zM5 11h14V8h-2v2h-2V8h-2v2h-2V8H9v2H7V8H5v3z",
    },
  },
  {
    // AFK Stages → chess-knight (horse head silhouette)
    keywords: ["afk stages"],
    icon: {
      color: "#60a5fa",
      path: "M5 22h14v-2H5v2zM6 20l1-4 2-2-1-2-3 1 1-3 2-1V7l3-3 4 1c2 1 3 3 3 5v10H6z",
    },
  },
  {
    // Arcane Labyrinth → dungeon (arched gate)
    keywords: ["arcane labyrinth", "labyrinth"],
    icon: {
      color: "#22d3ee",
      path: "M3 21h18M5 21V10a7 7 0 0 1 14 0v11M9 21v-7a3 3 0 0 1 6 0v7",
    },
  },
  {
    // Arena → swords (crossed)
    keywords: ["arena"],
    icon: {
      color: "#f87171",
      path: "M14.5 17.5 21 11l-3-3-6.5 6.5M3 21l4-4 3 3-4 4-3-3zM14 4l6 6-9 9-6-6 9-9z",
    },
  },
  {
    // Dream Realm → cloud-moon
    keywords: ["dream realm", "dream"],
    icon: {
      color: "#a78bfa",
      path: "M17 18a4 4 0 0 0-2-7.5 6 6 0 0 0-11 0A4 4 0 0 0 5 18h12zM18 3a4 4 0 0 0 4 6 6 6 0 0 1-6-6h2z",
    },
  },
  {
    // Dura's Trials → scroll
    keywords: ["dura"],
    icon: {
      color: "#facc15",
      path: "M21 6v12a3 3 0 0 1-3 3H7a3 3 0 0 1-3-3V8a2 2 0 0 1 2-2h13zM21 6V4a2 2 0 0 0-4 0v2M7 10h8M7 14h8",
    },
  },
  {
    // Season Legend Trial → tower-observation
    keywords: ["season legend", "legend trial", "legend"],
    icon: {
      color: "#fb923c",
      path: "M12 22V2M8 22l4-7 4 7M5 22h14M9 15V8h6v7M10 8V5h4v3",
    },
  },
  {
    // Dailies → calendar-check
    keywords: ["dailies", "daily", "chore"],
    icon: {
      color: "#34d399",
      path: "M19 4H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2zM3 10h18M8 2v4M16 2v4M9 16l2 2 4-4",
    },
  },
  {
    // Homestead → house with chimney
    keywords: ["homestead", "orders helper"],
    icon: {
      color: "#f472b6",
      path: "M3 11l9-8 9 8M5 9v11h5v-6h4v6h5V9M16 4v3",
    },
  },

  // ===== Events =====
  {
    keywords: ["fishing"],
    icon: {
      color: "#22d3ee",
      path: "M3 18c0-4 3-7 7-7m0 0c1-3 4-5 7-4m-7 4 1.5 1.5M12 8a1 1 0 1 0 0-2 1 1 0 0 0 0 2zm6 2c0 3.3-2.7 6-6 6S6 13.3 6 10",
    },
  },
  {
    keywords: ["matching cards", "matching"],
    icon: {
      color: "#fb923c",
      path: "M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3M3 16v3a2 2 0 0 0 2 2h3m8 0h3a2 2 0 0 0 2-2v-3",
    },
  },
  {
    // Synergy & CC → handshake
    keywords: ["synergy", "corrupt"],
    icon: {
      color: "#a78bfa",
      path: "M11 17 7 13l3-3 3 3 3-3 3 3-3 3-3-3M3 13l4-4M21 13l-4-4M9 18h6",
    },
  },
  {
    keywords: ["frostfire", "frost"],
    icon: {
      color: "#f87171",
      path: "M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z",
    },
  },
  {
    // Sunlit Showdown → sun (yellow)
    keywords: ["sunlit", "sun"],
    icon: {
      color: "#facc15",
      path: "M12 3v1M12 20v1M4.22 4.22l.7.7M18.36 18.36l.7.7M3 12H2M22 12h-1M4.92 19.07l.7-.7M18.36 5.64l.7-.7M12 7a5 5 0 1 0 0 10A5 5 0 0 0 12 7z",
    },
  },
  {
    // Available Quests → scroll (green)
    keywords: ["quest", "quests"],
    icon: {
      color: "#34d399",
      path: "M21 6v12a3 3 0 0 1-3 3H7a3 3 0 0 1-3-3V8a2 2 0 0 1 2-2h13zM21 6V4a2 2 0 0 0-4 0v2M7 10h8M7 14h8",
    },
  },
  {
    // Titan Reaver → skull
    keywords: ["titan reaver", "titan", "reaver"],
    icon: {
      color: "#f472b6",
      path: "M12 3a8 8 0 0 0-8 8c0 3 1.5 5 3 6v3h2v-2h2v2h2v-2h2v2h2v-3c1.5-1 3-3 3-6a8 8 0 0 0-8-8zM9 11a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3zM15 11a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3zM10 16h4",
    },
  },
  {
    // AFKJ Tracker → radar / scan
    keywords: ["tracker", "scan", "afkj"],
    icon: {
      color: "#60a5fa",
      path: "M21 21l-4.35-4.35M11 19a8 8 0 1 1 0-16 8 8 0 0 1 0 16zM11 7v4l3 2",
    },
  },

  // ===== Other / Routines =====
  {
    // Bare "stages" routine (no "afk") → layer-group, purple
    // Must come AFTER afk-stages entries above so those win first.
    keywords: ["stages", "stage", "progression"],
    icon: {
      color: "#a78bfa",
      path: "M12 2 2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5",
    },
  },
  {
    // Custom Routines → layer-group, slate
    keywords: ["custom routine", "custom", "routine"],
    icon: {
      color: "#94a3b8",
      path: "M12 2 2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5",
    },
  },
];

const fallbackIcon: TaskIcon = {
  color: "var(--text-3)",
  path: "M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9L13 2zM13 2v7h7",
};

export function getTaskIcon(label: string): TaskIcon {
  const lower = label.toLowerCase();
  for (const { keywords, icon } of iconMap) {
    if (keywords.some((k) => lower.includes(k))) return icon;
  }
  return fallbackIcon;
}
