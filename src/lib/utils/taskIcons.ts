// Inline SVG paths and accent colors for known task labels.
// Keys are lowercase substrings matched against the task label.
// Falls back to a generic icon when no match is found.

interface TaskIcon {
  path: string;
  color: string;
}

const iconMap: Array<{ keywords: string[]; icon: TaskIcon }> = [
  // AFK Journey — Events
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
    keywords: ["synergy", "corrupt"],
    icon: {
      color: "#a78bfa",
      path: "M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M23 21v-2a4 4 0 0 1 0-7.75M16 3.13a4 4 0 0 1 0 7.75M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z",
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
    keywords: ["sunlit", "sun"],
    icon: {
      color: "#fb923c",
      path: "M12 3v1M12 20v1M4.22 4.22l.7.7M18.36 18.36l.7.7M3 12H2M22 12h-1M4.92 19.07l.7-.7M18.36 5.64l.7-.7M12 7a5 5 0 1 0 0 10A5 5 0 0 0 12 7z",
    },
  },
  {
    keywords: ["quest", "quests"],
    icon: {
      color: "#34d399",
      path: "M12 20h9M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z",
    },
  },
  {
    keywords: ["titan reaver", "titan"],
    icon: {
      color: "#f472b6",
      path: "M12 2 2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5",
    },
  },
  {
    keywords: ["tracker", "scan", "afkj"],
    icon: {
      color: "#60a5fa",
      path: "M21 21l-4.35-4.35M11 19a8 8 0 1 1 0-16 8 8 0 0 1 0 16zM11 7v4l3 2",
    },
  },
  // AFK Journey — Combat
  {
    keywords: ["arena"],
    icon: {
      color: "#facc15",
      path: "M8 21h8M12 17v4M7 4v8a5 5 0 0 0 10 0V4M5 4h14",
    },
  },
  {
    keywords: ["tower"],
    icon: {
      color: "#22d3ee",
      path: "M3 21h18M9 21V7l3-4 3 4v14M9 21h6M12 7v5M9 12h6",
    },
  },
  {
    keywords: ["guild", "hunt"],
    icon: {
      color: "#a78bfa",
      path: "M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75",
    },
  },
  {
    keywords: ["pvp", "battle", "combat"],
    icon: {
      color: "#f87171",
      path: "M14.5 10c-.83 0-1.5-.67-1.5-1.5v-5c0-.83.67-1.5 1.5-1.5s1.5.67 1.5 1.5v5c0 .83-.67 1.5-1.5 1.5zM20.5 10H19V8.5c0-.83.67-1.5 1.5-1.5s1.5.67 1.5 1.5-.67 1.5-1.5 1.5zM9.5 14c.83 0 1.5.67 1.5 1.5v5c0 .83-.67 1.5-1.5 1.5S8 21.33 8 20.5v-5c0-.83.67-1.5 1.5-1.5zM3.5 14H5v1.5c0 .83-.67 1.5-1.5 1.5S2 16.33 2 15.5 2.67 14 3.5 14zM14 14.5c0-.83.67-1.5 1.5-1.5h5c.83 0 1.5.67 1.5 1.5s-.67 1.5-1.5 1.5h-5c-.83 0-1.5-.67-1.5-1.5zM15.5 9H14v1.5c0 .83.67 1.5 1.5 1.5s1.5-.67 1.5-1.5S16.33 9 15.5 9zM9.5 10c.83 0 1.5-.67 1.5-1.5v-5c0-.83-.67-1.5-1.5-1.5S8 2.67 8 3.5v5c0 .83.67 1.5 1.5 1.5zM10 9.5V11h1.5c.83 0 1.5-.67 1.5-1.5S12.33 8 11.5 8 10 8.67 10 9.5z",
    },
  },
  // Stages / progression (must come before "routine" so "stage progression" matches first)
  {
    keywords: ["stage", "progression"],
    icon: {
      color: "#a78bfa",
      path: "M3 21h4v-7H3zM10 21h4V10h-4zM17 21h4V3h-4z",
    },
  },
  // Routines / Custom
  {
    keywords: ["routine", "custom"],
    icon: {
      color: "#a78bfa",
      path: "M12 3 2 9l10 6 10-6-10-6zM2 15l10 6 10-6M2 12l10 6 10-6",
    },
  },
  // Dailies / chores
  {
    keywords: ["daily", "dailies", "chore"],
    icon: {
      color: "#34d399",
      path: "M3 4h18v4H3zM3 10h18v4H3zM3 16h18v4H3z",
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
