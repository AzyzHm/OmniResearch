interface AssistantBotProps {
  className?: string
  /**
   * "auto" (default) uses CSS variables that adapt to the current site
   * theme — right for placement on a normal surface (e.g. Hero's card).
   * "onDark" uses fixed light-on-dark colors, for placement on a surface
   * that's always dark regardless of site theme (e.g. AuthLayout's brand
   * panel, which is deliberately pinned to stay dark in both themes).
   */
  scheme?: "auto" | "onDark"
}

function AssistantBot({ className, scheme = "auto" }: AssistantBotProps) {
  const colors =
    scheme === "onDark"
      ? {
          head: "color-mix(in srgb, #F1F3F0 10%, transparent)",
          headStroke: "color-mix(in srgb, #F1F3F0 45%, transparent)",
          ink: "#F1F3F0",
          teal: "#4C9285",
          amber: "#D9A548",
          ringStroke: "color-mix(in srgb, #4C9285 35%, transparent)",
        }
      : {
          head: "var(--color-surface)",
          headStroke: "var(--color-teal)",
          ink: "var(--color-ink)",
          teal: "var(--color-teal)",
          amber: "var(--color-amber)",
          ringStroke: "color-mix(in srgb, var(--color-teal) 30%, transparent)",
        }

  return (
    <svg
      viewBox="0 0 200 200"
      className={className}
      role="img"
      aria-label="Animated illustration of the OmniResearch AI assistant"
    >
      {/* Slowly rotating orbit ring, echoing the app's orbital-rings logo mark */}
      <g className="bot-orbit-ring" style={{ transformOrigin: "100px 95px" }}>
        <circle
          cx="100"
          cy="95"
          r="72"
          fill="none"
          stroke={colors.ringStroke}
          strokeWidth="1.5"
          strokeDasharray="3 7"
        />
      </g>

      {/* Orbiting particles */}
      <g className="bot-orbit-fast" style={{ transformOrigin: "100px 95px" }}>
        <circle cx="172" cy="95" r="4" fill={colors.amber} />
      </g>
      <g className="bot-orbit-slow" style={{ transformOrigin: "100px 95px" }}>
        <circle cx="28" cy="95" r="3" fill={colors.teal} />
      </g>

      {/* Body: floats gently up and down */}
      <g className="bot-float">
        {/* Antenna */}
        <line
          x1="100"
          y1="47"
          x2="100"
          y2="32"
          stroke={colors.teal}
          strokeWidth="2.5"
          strokeLinecap="round"
        />
        <g className="bot-spark-pulse" style={{ transformOrigin: "100px 22px" }}>
          <path
            d="M100 11 L104 19 L112 23 L104 27 L100 35 L96 27 L88 23 L96 19 Z"
            fill={colors.amber}
          />
        </g>

        {/* Head */}
        <rect
          x="53"
          y="47"
          width="94"
          height="82"
          rx="30"
          fill={colors.head}
          stroke={colors.headStroke}
          strokeWidth="2.5"
        />

        {/* Eyes: blink periodically */}
        <g className="bot-blink" style={{ transformOrigin: "100px 87px" }}>
          <circle cx="81" cy="87" r="6.5" fill={colors.ink} />
          <circle cx="119" cy="87" r="6.5" fill={colors.ink} />
        </g>

        {/* Smile */}
        <path
          d="M84 105 Q100 115 116 105"
          fill="none"
          stroke={colors.ink}
          strokeWidth="2.5"
          strokeLinecap="round"
        />
      </g>
    </svg>
  )
}

export default AssistantBot
