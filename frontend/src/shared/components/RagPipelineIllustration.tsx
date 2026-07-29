interface RagPipelineIllustrationProps {
  className?: string
}

function RagPipelineIllustration({ className }: RagPipelineIllustrationProps) {
  return (
    <svg
      viewBox="0 0 620 600"
      className={className}
      role="img"
      aria-label="Illustration of a prompt flowing through a router, a retrieve-rerank-validate loop that fetches missing info on retry, into an AI assistant that produces a cited answer traced back to its source"
    >
      {/* Trace-back leader from the answer to the source documents */}
      <path
        d="M240,518 C120,560 40,400 100,240"
        fill="none"
        stroke="var(--color-teal)"
        strokeWidth="1.2"
        className="pipeline-leader-flow"
        opacity="0.5"
      />

      {/* Source documents */}
      <g className="pipeline-doc2">
        <rect x="60" y="175" width="60" height="48" rx="6" fill="var(--color-surface)" stroke="var(--color-teal)" strokeWidth="1.5" />
        <line x1="70" y1="188" x2="110" y2="188" stroke="var(--color-teal)" strokeWidth="1.3" opacity="0.5" />
        <line x1="70" y1="197" x2="104" y2="197" stroke="var(--color-teal)" strokeWidth="1.3" opacity="0.5" />
        <line x1="70" y1="206" x2="108" y2="206" stroke="var(--color-teal)" strokeWidth="1.3" opacity="0.5" />
      </g>
      <g className="pipeline-doc1">
        <rect x="45" y="195" width="60" height="48" rx="6" fill="var(--color-surface)" stroke="var(--color-amber)" strokeWidth="1.5" />
        <line x1="55" y1="208" x2="95" y2="208" stroke="var(--color-amber)" strokeWidth="1.3" opacity="0.5" />
        <line x1="55" y1="217" x2="89" y2="217" stroke="var(--color-amber)" strokeWidth="1.3" opacity="0.5" />
        <line x1="55" y1="226" x2="93" y2="226" stroke="var(--color-amber)" strokeWidth="1.3" opacity="0.5" />
      </g>
      <g className="pipeline-doc3">
        <rect x="52" y="215" width="60" height="48" rx="6" fill="var(--color-surface)" stroke="var(--color-ink)" strokeWidth="1.1" opacity="0.9" />
        <line x1="62" y1="228" x2="102" y2="228" stroke="var(--color-ink)" strokeWidth="1.3" opacity="0.4" />
        <line x1="62" y1="237" x2="96" y2="237" stroke="var(--color-ink)" strokeWidth="1.3" opacity="0.4" />
        <line x1="62" y1="246" x2="100" y2="246" stroke="var(--color-ink)" strokeWidth="1.3" opacity="0.4" />
      </g>
      <text x="82" y="270" textAnchor="middle" fontSize="11" fill="var(--color-ink)" fontFamily="monospace" opacity="0.6">
        sources
      </text>

      {/* Prompt */}
      <rect x="395" y="45" width="130" height="40" rx="16" fill="var(--color-ink)" />
      <text x="460" y="70" textAnchor="middle" fontSize="12" fill="var(--color-paper)" fontFamily="monospace" className="pipeline-bubble">
        prompt
      </text>
      <path d="M460,85 L460,112" stroke="var(--color-teal)" strokeWidth="2" fill="none" />

      {/* Router */}
      <g className="pipeline-router">
        <path d="M460,110 L480,130 L460,150 L440,130 Z" fill="var(--color-ink)" stroke="var(--color-teal)" strokeWidth="1.5" />
      </g>
      <text x="460" y="98" textAnchor="middle" fontSize="11" fill="var(--color-ink)" fontFamily="monospace" opacity="0.7">
        router
      </text>

      {/* Main flow: router -> retrieve, and the skip path -> assistant */}
      <path className="pipeline-flow-main" d="M445,140 Q350,170 243,198" fill="none" stroke="var(--color-teal)" strokeWidth="1.5" opacity="0.55" />
      <path className="pipeline-flow-skip" d="M478,140 Q520,300 320,392" fill="none" stroke="var(--color-amber)" strokeWidth="1.2" opacity="0.35" />
      <text x="500" y="270" fontSize="10" fill="var(--color-amber)" fontFamily="monospace" opacity="0.6">
        no retrieval needed
      </text>

      {/* Retrieve -> rerank -> validate -> assistant */}
      <path className="pipeline-flow-main" d="M150,205 Q190,190 230,205" fill="none" stroke="var(--color-teal)" strokeWidth="1.5" opacity="0.55" />
      <path className="pipeline-flow-main" d="M243,205 L347,205" fill="none" stroke="var(--color-teal)" strokeWidth="1.5" opacity="0.55" />
      <path className="pipeline-flow-main" d="M360,218 L360,287" fill="none" stroke="var(--color-teal)" strokeWidth="1.5" opacity="0.55" />
      <path className="pipeline-flow-main" d="M360,313 Q340,360 305,392" fill="none" stroke="var(--color-teal)" strokeWidth="1.5" opacity="0.55" />

      {/* Validate's real retry loop, back to retrieve */}
      <path className="pipeline-flow-retry" d="M347,300 Q260,320 220,260 Q210,240 220,220" fill="none" stroke="var(--color-amber)" strokeWidth="1.5" opacity="0.6" />
      <text x="250" y="335" textAnchor="middle" fontSize="10" fill="var(--color-amber)" fontFamily="monospace">
        fetch missing info
      </text>

      {/* Traveling packets along the main flow and the retry loop */}
      <circle className="pipeline-packet-main" r="4" fill="var(--color-teal)" />
      <circle className="pipeline-packet-retry" r="3.5" fill="var(--color-amber)" />

      {/* Pipeline stage nodes */}
      <g className="pipeline-node-retrieve">
        <circle cx="230" cy="205" r="13" fill="var(--color-teal)" />
      </g>
      <text x="230" y="240" textAnchor="middle" fontSize="11" fill="var(--color-ink)" fontFamily="monospace">
        retrieve
      </text>
      <g className="pipeline-node-rerank">
        <circle cx="360" cy="205" r="13" fill="var(--color-teal)" />
      </g>
      <text x="360" y="182" textAnchor="middle" fontSize="11" fill="var(--color-ink)" fontFamily="monospace">
        rerank
      </text>
      <g className="pipeline-node-validate">
        <circle cx="360" cy="300" r="13" fill="var(--color-amber)" />
      </g>
      <text x="400" y="304" textAnchor="middle" fontSize="11" fill="var(--color-ink)" fontFamily="monospace">
        validate
      </text>

      {/* Orbit particles around the assistant */}
      <g className="bot-orbit-slow" style={{ transformOrigin: "300px 432px" }}>
        <circle cx="240" cy="435" r="3" fill="var(--color-teal)" />
      </g>
      <g className="bot-orbit-fast" style={{ transformOrigin: "300px 432px" }}>
        <circle cx="358" cy="435" r="4" fill="var(--color-amber)" />
      </g>

      {/* The assistant */}
      <g className="bot-float" style={{ transformOrigin: "300px 432px" }}>
        <line x1="300" y1="395" x2="300" y2="378" stroke="var(--color-teal)" strokeWidth="2.5" strokeLinecap="round" />
        <g className="bot-spark-pulse" style={{ transformOrigin: "300px 368px" }}>
          <path
            d="M300,364 L303,371 L310,374 L303,377 L300,384 L297,377 L290,374 L297,371 Z"
            fill="var(--color-amber)"
          />
        </g>
        <rect x="255" y="395" width="90" height="75" rx="26" fill="var(--color-surface)" stroke="var(--color-teal)" strokeWidth="2.2" />
        <g className="bot-blink" style={{ transformOrigin: "300px 432px" }}>
          <circle cx="280" cy="432" r="6" fill="var(--color-ink)" />
          <circle cx="320" cy="432" r="6" fill="var(--color-ink)" />
        </g>
        <path d="M282,450 Q300,459 318,450" fill="none" stroke="var(--color-ink)" strokeWidth="2.3" strokeLinecap="round" />
      </g>

      {/* Answer with citation, tracing back to the sources */}
      <rect x="250" y="493" width="140" height="52" rx="16" fill="var(--color-surface)" stroke="var(--color-teal)" strokeWidth="1.8" />
      <text x="320" y="513" textAnchor="middle" fontSize="12" fill="var(--color-ink)" fontFamily="monospace">
        answer
      </text>
      <g className="pipeline-badge">
        <circle cx="320" cy="530" r="9" fill="var(--color-ink)" />
        <text x="320" y="534" textAnchor="middle" fontSize="10" fill="var(--color-paper)" fontFamily="monospace">
          1
        </text>
      </g>
    </svg>
  )
}

export default RagPipelineIllustration