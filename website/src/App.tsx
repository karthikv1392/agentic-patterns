import { useEffect, useMemo, useState } from "react";
import {
  categoryCounts,
  patterns,
  type Pattern,
  type PatternCategory,
  type QualityAttribute,
  type QualityImpact,
} from "./patterns";

const categories: Array<"All" | PatternCategory> = [
  "All",
  "Single agent",
  "Multi-agent",
  "Memory",
];

const qualityAttributes = Array.from(new Set(patterns.flatMap((pattern) => [
  ...pattern.qualityAttributes,
  ...pattern.benefits.map((impact) => impact.attribute),
  ...pattern.liabilities.map((impact) => impact.attribute),
]))).sort((left, right) => left.localeCompare(right));

type PatternRecommendation = {
  pattern: Pattern;
  score: number;
  gains: QualityImpact[];
  conflicts: QualityImpact[];
  protectedRisks: QualityImpact[];
  primaryMatches: QualityAttribute[];
};

function categoryClass(category: PatternCategory) {
  return category.toLowerCase().replaceAll(" ", "-");
}

function PatternVisual({ pattern, compact = false }: { pattern: Pattern; compact?: boolean }) {
  return (
    <div
      className={`pattern-visual ${categoryClass(pattern.category)} ${compact ? "compact" : ""}`}
      aria-label={`${pattern.name} architecture: ${pattern.flow.join(" to ")}`}
    >
      <div className="visual-orbit orbit-one" />
      <div className="visual-orbit orbit-two" />
      <div className="visual-flow">
        {pattern.flow.map((node, index) => (
          <div className="visual-step" key={node}>
            <div className="visual-node">
              <span className="node-index">{String(index + 1).padStart(2, "0")}</span>
              <span>{node}</span>
            </div>
            {index < pattern.flow.length - 1 && <span className="visual-arrow">→</span>}
          </div>
        ))}
      </div>
    </div>
  );
}

function SequenceDiagram({ pattern }: { pattern: Pattern }) {
  const { participants, messages } = pattern.sequence;
  const width = Math.max(720, participants.length * 150);
  const height = 150 + messages.length * 56;
  const margin = 78;
  const step = participants.length > 1 ? (width - margin * 2) / (participants.length - 1) : 0;
  const positions = participants.map((_, index) => margin + step * index);
  const arrowId = `sequence-arrow-${pattern.id}`;

  return (
    <div className="sequence-shell">
      <svg
        className="sequence-diagram"
        viewBox={`0 0 ${width} ${height}`}
        width={width}
        height={height}
        role="img"
        aria-labelledby={`sequence-title-${pattern.id} sequence-description-${pattern.id}`}
      >
        <title id={`sequence-title-${pattern.id}`}>{pattern.name} sequence diagram</title>
        <desc id={`sequence-description-${pattern.id}`}>
          {messages.map((message) => `${participants[message.from]} sends ${message.label} to ${participants[message.to]}`).join(". ")}
        </desc>
        <defs>
          <marker id={arrowId} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" />
          </marker>
        </defs>

        {participants.map((participant, index) => (
          <g className="sequence-participant" key={participant}>
            <rect x={positions[index] - 65} y="10" width="130" height="42" />
            <text x={positions[index]} y="36" textAnchor="middle">{participant}</text>
            <line x1={positions[index]} y1="52" x2={positions[index]} y2={height - 52} />
            <rect x={positions[index] - 65} y={height - 52} width="130" height="42" />
            <text x={positions[index]} y={height - 26} textAnchor="middle">{participant}</text>
          </g>
        ))}

        {messages.map((message, index) => {
          const x1 = positions[message.from];
          const x2 = positions[message.to];
          const y = 88 + index * 56;
          const isSelf = message.from === message.to;

          return (
            <g className={`sequence-message ${message.reply ? "reply" : "call"}`} key={`${message.label}-${index}`}>
              <text className="sequence-step" x="18" y={y + 4}>{String(index + 1).padStart(2, "0")}</text>
              {isSelf ? (
                <>
                  <path d={`M ${x1} ${y} H ${x1 + 58} V ${y + 28} H ${x1 + 8}`} markerEnd={`url(#${arrowId})`} />
                  <text x={x1 + 30} y={y - 9} textAnchor="middle">{message.label}</text>
                </>
              ) : (
                <>
                  <line x1={x1} y1={y} x2={x2} y2={y} markerEnd={`url(#${arrowId})`} />
                  <text x={(x1 + x2) / 2} y={y - 9} textAnchor="middle">{message.label}</text>
                </>
              )}
            </g>
          );
        })}
      </svg>
    </div>
  );
}

function PatternCard({ pattern, onOpen }: { pattern: Pattern; onOpen: () => void }) {
  return (
    <button className="pattern-card" onClick={onOpen} aria-label={`Explore ${pattern.name}`}>
      <PatternVisual pattern={pattern} compact />
      <div className="card-body">
        <div className="card-kicker">
          <span className={`category-dot ${categoryClass(pattern.category)}`} />
          <span>{pattern.category}</span>
          <span className="kicker-line" />
          <span>{pattern.number}</span>
        </div>
        <h3>{pattern.name}</h3>
        <p>{pattern.summary}</p>
        <div className="card-meta">
          <span>{pattern.complexity}</span>
          <span>{pattern.calls}</span>
          <span>{pattern.tools ? "Tools" : "No tools"}</span>
        </div>
        <div className="card-link">
          Study pattern <span aria-hidden="true">↗</span>
        </div>
      </div>
    </button>
  );
}

function PatternDetail({ pattern, onClose }: { pattern: Pattern; onClose: () => void }) {
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKeyDown);
    document.body.classList.add("modal-open");
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.classList.remove("modal-open");
    };
  }, [onClose]);

  async function copyCode() {
    await navigator.clipboard.writeText(pattern.code.snippet);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  }

  return (
    <div className="detail-backdrop" onMouseDown={onClose}>
      <article
        className="detail-panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="detail-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="detail-topbar">
          <a className="wordmark small" href="#top" onClick={onClose}>
            <span className="wordmark-mark">AP</span>
            <span>Pattern field guide</span>
          </a>
          <button className="close-button" onClick={onClose} aria-label="Close pattern detail">
            Close <span aria-hidden="true">×</span>
          </button>
        </div>

        <header className="detail-hero">
          <div className="detail-heading">
            <div className="eyebrow">
              <span>{pattern.category}</span>
              <span>/</span>
              <span>{pattern.number}</span>
            </div>
            <h2 id="detail-title">{pattern.name}</h2>
            <p>{pattern.summary}</p>
            <div className="detail-facts">
              <div><span>Level</span><strong>{pattern.complexity}</strong></div>
              <div><span>Model work</span><strong>{pattern.calls}</strong></div>
              <div><span>Implementation</span><strong>{pattern.files} {pattern.files === 1 ? "file" : "files"}</strong></div>
            </div>
          </div>
          <PatternVisual pattern={pattern} />
        </header>

        <div className="detail-content">
          <main className="detail-main">
            <section className="cps-grid" aria-label="Pattern explanation">
              <div className="cps-card">
                <span className="cps-number">01</span>
                <div><h3>Context</h3><p>{pattern.context}</p></div>
              </div>
              <div className="cps-card problem">
                <span className="cps-number">02</span>
                <div>
                  <h3>Problem</h3>
                  <div className="quality-tags" aria-label="Primary quality attributes">
                    {pattern.qualityAttributes.map((attribute) => <span key={attribute}>{attribute}</span>)}
                  </div>
                  <p>{pattern.problem}</p>
                </div>
              </div>
              <div className="cps-card solution">
                <span className="cps-number">03</span>
                <div><h3>Solution</h3><p>{pattern.solution}</p></div>
              </div>
            </section>

            <section className={`sequence-section ${categoryClass(pattern.category)}`} aria-label="Interaction sequence">
              <div className="section-heading-row">
                <div>
                  <span className="section-overline">Runtime collaboration</span>
                  <h3>Interaction sequence</h3>
                </div>
                <p className="quality-intro">Follow the calls, handoffs, and return messages from left to right.</p>
              </div>
              <SequenceDiagram pattern={pattern} />
              <div className="sequence-legend" aria-hidden="true">
                <span><i className="solid" /> Request or handoff</span>
                <span><i className="dashed" /> Return or response</span>
                <span>Scroll horizontally on smaller screens →</span>
              </div>
            </section>

            <section className="quality-section" aria-label="Quality attribute trade-offs">
              <div className="section-heading-row">
                <div>
                  <span className="section-overline">Architectural consequences</span>
                  <h3>Quality attribute trade-offs</h3>
                </div>
                <p className="quality-intro">The pattern strengthens some system qualities while placing pressure on others.</p>
              </div>
              <div className="quality-columns">
                <div className="quality-column benefits">
                  <div className="quality-column-heading"><span>+</span><h4>Pros — quality gains</h4></div>
                  {pattern.benefits.map((impact) => (
                    <div className="quality-impact" key={`${impact.attribute}-${impact.explanation}`}>
                      <strong>{impact.attribute}</strong>
                      <p>{impact.explanation}</p>
                    </div>
                  ))}
                </div>
                <div className="quality-column liabilities">
                  <div className="quality-column-heading"><span>−</span><h4>Cons — quality costs</h4></div>
                  {pattern.liabilities.map((impact) => (
                    <div className="quality-impact" key={`${impact.attribute}-${impact.explanation}`}>
                      <strong>{impact.attribute}</strong>
                      <p>{impact.explanation}</p>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            <section className="code-section">
              <div className="section-heading-row">
                <div>
                  <span className="section-overline">From the runnable repository</span>
                  <h3>Implementation sketch</h3>
                </div>
                <button className="copy-button" onClick={copyCode}>
                  {copied ? "Copied" : "Copy code"}
                </button>
              </div>
              <div className="code-window">
                <div className="code-titlebar">
                  <span className="window-dots" aria-hidden="true"><i /><i /><i /></span>
                  <span>{pattern.code.path}</span>
                  <span>Python</span>
                </div>
                <pre><code>{pattern.code.snippet}</code></pre>
              </div>
            </section>
          </main>

          <aside className="detail-aside">
            <section>
              <span className="section-overline">Use this when</span>
              <ul className="use-list">
                {pattern.useWhen.map((item) => <li key={item}>{item}</li>)}
              </ul>
            </section>
            <section className="tradeoff-card">
              <span className="section-overline">Design tension</span>
              <p>{pattern.tradeoff}</p>
            </section>
            <section className="implementation-card">
              <span className="section-overline">Repository facts</span>
              <dl>
                <div><dt>Tool use</dt><dd>{pattern.tools ? "Yes" : "No"}</dd></div>
                <div><dt>Source files</dt><dd>{pattern.files}</dd></div>
                <div><dt>Runtime</dt><dd>Python</dd></div>
                <div><dt>Interface</dt><dd>Streamlit</dd></div>
              </dl>
            </section>
          </aside>
        </div>
      </article>
    </div>
  );
}

export default function Home() {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState<"All" | PatternCategory>("All");
  const [selected, setSelected] = useState<Pattern | null>(null);
  const [optimizeFor, setOptimizeFor] = useState<QualityAttribute[]>([]);
  const [protect, setProtect] = useState<QualityAttribute[]>([]);

  const filteredPatterns = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return patterns.filter((pattern) => {
      const matchesCategory = category === "All" || pattern.category === category;
      const haystack = [
        pattern.name,
        pattern.summary,
        pattern.context,
        pattern.problem,
        pattern.solution,
        pattern.category,
        ...pattern.qualityAttributes,
        ...pattern.benefits.map((impact) => `${impact.attribute} ${impact.explanation}`),
        ...pattern.liabilities.map((impact) => `${impact.attribute} ${impact.explanation}`),
        ...pattern.sequence.participants,
        ...pattern.sequence.messages.map((message) => message.label),
      ].join(" ").toLowerCase();
      return matchesCategory && (!normalizedQuery || haystack.includes(normalizedQuery));
    });
  }, [category, query]);

  const recommendations = useMemo<PatternRecommendation[]>(() => {
    if (optimizeFor.length === 0) return [];

    return patterns
      .map((pattern) => {
        const gains = pattern.benefits.filter((impact) => optimizeFor.includes(impact.attribute));
        const conflicts = pattern.liabilities.filter((impact) => optimizeFor.includes(impact.attribute));
        const protectedRisks = pattern.liabilities.filter((impact) => protect.includes(impact.attribute));
        const protectedGains = pattern.benefits.filter((impact) => protect.includes(impact.attribute));
        const primaryMatches = pattern.qualityAttributes.filter((attribute) => optimizeFor.includes(attribute));
        const score = gains.length * 3
          + primaryMatches.length
          + protectedGains.length
          - conflicts.length * 2
          - protectedRisks.length * 3;

        return { pattern, score, gains, conflicts, protectedRisks, primaryMatches };
      })
      .sort((left, right) => (
        right.score - left.score
        || right.gains.length - left.gains.length
        || left.pattern.name.localeCompare(right.pattern.name)
      ))
      .slice(0, 5);
  }, [optimizeFor, protect]);

  function toggleOptimize(attribute: QualityAttribute) {
    setOptimizeFor((current) => current.includes(attribute)
      ? current.filter((item) => item !== attribute)
      : [...current, attribute]);
    setProtect((current) => current.filter((item) => item !== attribute));
  }

  function toggleProtect(attribute: QualityAttribute) {
    setProtect((current) => current.includes(attribute)
      ? current.filter((item) => item !== attribute)
      : [...current, attribute]);
    setOptimizeFor((current) => current.filter((item) => item !== attribute));
  }

  function resetRecommendations() {
    setOptimizeFor([]);
    setProtect([]);
  }

  function openPattern(pattern: Pattern) {
    window.history.replaceState(null, "", `#pattern-${pattern.id}`);
    setSelected(pattern);
  }

  function closePattern() {
    window.history.replaceState(null, "", window.location.pathname);
    setSelected(null);
  }

  return (
    <>
      <main id="top">
        <nav className="site-nav" aria-label="Primary navigation">
          <a className="wordmark" href="#top">
            <span className="wordmark-mark">AP</span>
            <span>Agentic AI patterns</span>
          </a>
          <div className="nav-links">
            <a href="#catalog">Catalog</a>
            <a href="#recommend">Recommend</a>
            <a href="#about">Method</a>
            <a className="nav-cta" href="#run">Run the examples <span>↗</span></a>
          </div>
        </nav>

        <section className="hero">
          <div className="hero-copy">
            <div className="eyebrow"><span>A curated learning guide</span><span>/</span><span>2026 edition</span></div>
            <h1>Architectural<br />Patterns for<br /><em>Agentic AI.</em></h1>
            <p className="hero-intro">
              A curated, non-exhaustive guide to architecturally relevant patterns for agentic AI. Rather than
              cataloguing every pattern, it helps learners and practitioners understand selected patterns through
              their context, quality-attribute forces, reusable solution, implementation, and runtime interactions.
            </p>
            <div className="hero-actions">
              <a className="primary-button" href="#recommend">Find a matching pattern <span>↓</span></a>
              <a className="text-link" href="#catalog">Browse all patterns <span>→</span></a>
            </div>
          </div>
          <div className="hero-system" aria-label="Agent system illustration">
            <div className="system-label">Pattern selection = architectural decision</div>
            <div className="system-stage stage-input"><span>01</span><strong>Context</strong><small>What recurs?</small></div>
            <div className="system-connector connector-one" />
            <div className="system-stage stage-pattern"><span>02</span><strong>Decision</strong><small>Which pattern fits?</small></div>
            <div className="system-connector connector-two" />
            <div className="system-stage stage-outcome"><span>03</span><strong>Consequences</strong><small>Which qualities change?</small></div>
            <div className="system-pulse pulse-one" />
            <div className="system-pulse pulse-two" />
          </div>
        </section>

        <section className="metrics" aria-label="Library summary">
          <div><strong>26</strong><span>Curated<br />patterns</span></div>
          <div><strong>03</strong><span>System<br />families</span></div>
          <div><strong>100%</strong><span>Runnable<br />examples</span></div>
          <div><strong>Local</strong><span>Ollama-first<br />runtime</span></div>
        </section>

        <section className="method" id="about">
          <div className="section-index">01 / Method</div>
          <div className="method-intro">
            <span className="section-overline">Why this guide exists</span>
            <h2>Learn reusable solutions through working implementations.</h2>
          </div>
          <div className="method-copy">
            <p>
              Frameworks change quickly, but recurring design problems and their architectural forces endure.
              This collection is intentionally illustrative rather than exhaustive: it brings together useful,
              recognizable patterns that help explain how agentic systems can be structured and how they work in
              practice. Choosing a pattern is an architectural decision with measurable consequences. Following
              software architecture literature, each entry states the context, quality attributes at risk, solution,
              benefits, liabilities, interaction sequence, and a runnable implementation.
            </p>
            <div className="method-steps">
              <div><span>Context</span><p>See the conditions that make the pattern relevant.</p></div>
              <div><span>Forces</span><p>Name the quality attributes in tension before choosing architecture.</p></div>
              <div><span>Trade-offs</span><p>Compare the measurable benefits and liabilities introduced by the solution.</p></div>
              <div><span>Solution</span><p>Understand the flow and connect it to a runnable implementation.</p></div>
            </div>
            <div className="method-reference">
              <span>Architecture basis</span>
              <p>
                Adapted from SEI quality-attribute and scenario-based analysis: qualities such as reliability,
                performance, security, modifiability, and usability drive architectural decisions, and every
                mechanism creates side effects on other qualities.
              </p>
              <div>
                <a href="https://sei.cmu.edu/library/reasoning-about-software-quality-attributes/" target="_blank" rel="noreferrer">Quality attribute reasoning ↗</a>
                <a href="https://www.sei.cmu.edu/library/quality-attribute-design-primitives/" target="_blank" rel="noreferrer">Design primitives ↗</a>
                <a href="https://insights.sei.cmu.edu/library/scenario-based-analysis-of-software-architecture/" target="_blank" rel="noreferrer">Scenario-based analysis ↗</a>
              </div>
            </div>
            <div className="method-reference scope-reference">
              <span>Scope &amp; influences</span>
              <p>
                This guide is not intended to be another comprehensive catalogue of agentic patterns. It builds on
                prior cataloguing work and curates a focused set of patterns with architectural relevance. Its distinct
                contribution is to connect each pattern to runnable implementation details, an interaction sketch, and
                SEI-style quality-attribute reasoning.
              </p>
              <ol className="source-list">
                <li>
                  <span>01</span>
                  <div>
                    <a href="https://doi.org/10.1016/j.jss.2024.112278" target="_blank" rel="noreferrer">
                      Liu, Y., Lo, S. K., Lu, Q., Zhu, L., Zhao, D., Xu, X., Harrer, S. &amp; Whittle, J. (2025).
                      Agent Design Pattern Catalogue ↗
                    </a>
                    <p>Journal of Systems and Software, 220, 112278.</p>
                  </div>
                </li>
                <li>
                  <span>02</span>
                  <div>
                    <a href="https://www.agentic-patterns.com/" target="_blank" rel="noreferrer">
                      Agentic Patterns — broad reference library ↗
                    </a>
                    <p>A wider catalogue for discovering patterns across agent architecture and product practice.</p>
                  </div>
                </li>
              </ol>
            </div>
          </div>
        </section>

        <section className="recommender" id="recommend">
          <div className="recommender-heading">
            <div>
              <div className="section-index">02 / Decision support</div>
              <span className="section-overline">Quality attribute recommender</span>
              <h2>Which patterns support your priorities?</h2>
            </div>
            <p>
              Select the qualities you want to improve and any qualities you cannot afford to weaken. The ranking
              uses the documented benefits, liabilities, and primary quality attributes in this guide.
            </p>
          </div>

          <div className="recommender-shell">
            <div className="attribute-builder">
              <fieldset>
                <legend><span>01</span> Optimize for</legend>
                <p>Choose one or more qualities the architecture should strengthen.</p>
                <div className="attribute-options">
                  {qualityAttributes.map((attribute) => (
                    <button
                      type="button"
                      key={`optimize-${attribute}`}
                      className={optimizeFor.includes(attribute) ? "selected optimize" : ""}
                      aria-pressed={optimizeFor.includes(attribute)}
                      onClick={() => toggleOptimize(attribute)}
                    >
                      <span aria-hidden="true">+</span>{attribute}
                    </button>
                  ))}
                </div>
              </fieldset>

              <fieldset>
                <legend><span>02</span> Protect from degradation</legend>
                <p>Optional: mark qualities that should not become an architectural liability.</p>
                <div className="attribute-options protect-options">
                  {qualityAttributes.map((attribute) => (
                    <button
                      type="button"
                      key={`protect-${attribute}`}
                      className={protect.includes(attribute) ? "selected protect" : ""}
                      aria-pressed={protect.includes(attribute)}
                      onClick={() => toggleProtect(attribute)}
                    >
                      <span aria-hidden="true">◇</span>{attribute}
                    </button>
                  ))}
                </div>
              </fieldset>

              <div className="score-key">
                <span>Scoring</span>
                <p><strong>+3</strong> documented benefit · <strong>+1</strong> primary match · <strong>−2</strong> desired-quality liability · <strong>−3</strong> protected-quality liability</p>
              </div>
            </div>

            <div className="recommendation-results" aria-live="polite">
              <div className="results-topbar">
                <div>
                  <span>Ranked suggestions</span>
                  <strong>{optimizeFor.length === 0 ? "Waiting for priorities" : `Top ${recommendations.length} of ${patterns.length} patterns`}</strong>
                </div>
                {(optimizeFor.length > 0 || protect.length > 0) && (
                  <button type="button" onClick={resetRecommendations}>Reset</button>
                )}
              </div>

              {optimizeFor.length === 0 ? (
                <div className="recommendation-empty">
                  <span>+</span>
                  <h3>Start with a quality attribute.</h3>
                  <p>For example, select Reliability, Security, or Latency to see patterns whose documented consequences align with that goal.</p>
                </div>
              ) : (
                <div className="recommendation-list">
                  {recommendations.map((recommendation, index) => {
                    const warnings = [...recommendation.conflicts, ...recommendation.protectedRisks]
                      .filter((impact, impactIndex, impacts) => impacts.findIndex((item) => item.attribute === impact.attribute) === impactIndex);

                    return (
                      <article className="recommendation-card" key={recommendation.pattern.id}>
                        <div className="recommendation-rank">{String(index + 1).padStart(2, "0")}</div>
                        <div className="recommendation-body">
                          <div className="recommendation-title">
                            <div>
                              <span>{recommendation.pattern.category}</span>
                              <h3>{recommendation.pattern.name}</h3>
                            </div>
                            <div className={`recommendation-score ${recommendation.score < 0 ? "negative" : ""}`}>
                              <strong>{recommendation.score > 0 ? `+${recommendation.score}` : recommendation.score}</strong>
                              <span>fit score</span>
                            </div>
                          </div>
                          <p>{recommendation.pattern.summary}</p>
                          <div className="recommendation-evidence">
                            <div>
                              <span>Strengthens</span>
                              <div>
                                {recommendation.gains.length > 0
                                  ? recommendation.gains.map((impact) => <i key={impact.attribute}>{impact.attribute}</i>)
                                  : <small>No direct documented benefit match</small>}
                              </div>
                            </div>
                            {warnings.length > 0 && (
                              <div className="warning">
                                <span>Watch</span>
                                <div>{warnings.map((impact) => <i key={impact.attribute}>{impact.attribute}</i>)}</div>
                              </div>
                            )}
                          </div>
                          <div className="recommendation-footer">
                            <p>{recommendation.pattern.tradeoff}</p>
                            <button type="button" onClick={() => openPattern(recommendation.pattern)}>Study pattern <span>↗</span></button>
                          </div>
                        </div>
                      </article>
                    );
                  })}
                </div>
              )}

              <p className="recommendation-disclaimer">
                Decision-support only. Validate each suggestion against a concrete quality-attribute scenario,
                system context, constraints, and measurable response before making an architectural decision.
              </p>
            </div>
          </div>
        </section>

        <section className="catalog" id="catalog">
          <div className="catalog-heading">
            <div>
              <div className="section-index">03 / Catalog</div>
              <span className="section-overline">Browse this collection</span>
              <h2>Explore recurring architectural shapes.</h2>
            </div>
            <label className="search-box">
              <span className="search-icon" aria-hidden="true">⌕</span>
              <span className="sr-only">Search patterns</span>
              <input
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search patterns, problems, ideas…"
              />
              {query && <button onClick={() => setQuery("")} aria-label="Clear search">×</button>}
            </label>
          </div>

          <div className="filter-row" role="group" aria-label="Filter by pattern family">
            {categories.map((item) => (
              <button
                key={item}
                className={category === item ? "active" : ""}
                onClick={() => setCategory(item)}
              >
                {item}
                <span>{item === "All" ? patterns.length : categoryCounts[item]}</span>
              </button>
            ))}
            <div className="result-count">Showing {filteredPatterns.length} patterns</div>
          </div>

          {filteredPatterns.length > 0 ? (
            <div className="pattern-grid">
              {filteredPatterns.map((pattern) => (
                <PatternCard key={`${pattern.category}-${pattern.id}`} pattern={pattern} onOpen={() => openPattern(pattern)} />
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <span>00</span>
              <h3>No matching pattern.</h3>
              <p>Try a broader term or return to the complete collection.</p>
              <button onClick={() => { setQuery(""); setCategory("All"); }}>Reset filters</button>
            </div>
          )}
        </section>

        <section className="run-section" id="run">
          <div className="run-copy">
            <div className="section-index light">04 / Repository</div>
            <span className="section-overline">Learn by running</span>
            <h2>Inspect the pattern.<br />Change the behavior.</h2>
            <p>
              Every entry maps to a self-contained Streamlit implementation. Run the unified launcher,
              compare execution traces, and swap the local model as you learn.
            </p>
            <div className="run-notes">
              <span>Python 3.9+</span>
              <span>Ollama</span>
              <span>Streamlit</span>
              <span>Local-first</span>
            </div>
          </div>
          <div className="terminal-card" aria-label="Repository quickstart commands">
            <div className="terminal-bar">
              <span className="window-dots"><i /><i /><i /></span>
              <span>agentic-patterns / quickstart</span>
            </div>
            <div className="terminal-body">
              <div><span className="prompt">$</span><code>ollama pull gemma4</code></div>
              <div><span className="prompt">$</span><code>cd agentic-patterns</code></div>
              <div><span className="prompt">$</span><code>./run.sh</code></div>
              <div className="terminal-output">Which demo would you like to run?</div>
              <div className="terminal-choice"><span>1</span> Single Agent Patterns <small>:8501</small></div>
              <div className="terminal-choice"><span>2</span> Multi Agent Patterns <small>:8502</small></div>
            </div>
          </div>
        </section>

        <footer>
          <a className="wordmark small" href="#top"><span className="wordmark-mark">AP</span><span>Agentic patterns</span></a>
          <p>Made with <span aria-label="love">♥</span> by <a href="https://karthikvaidhyanathan.com" target="_blank" rel="noreferrer">Karthik Vaidhyanathan</a></p>
          <a href="#top">Back to top ↑</a>
        </footer>
      </main>

      {selected && <PatternDetail pattern={selected} onClose={closePattern} />}
    </>
  );
}
