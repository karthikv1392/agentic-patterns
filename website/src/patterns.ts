export type PatternCategory = "Single agent" | "Multi-agent" | "Memory";

export type QualityAttribute =
  | "Accessibility"
  | "Accuracy"
  | "Adaptability"
  | "Auditability"
  | "Cost"
  | "Data freshness"
  | "Interoperability"
  | "Latency"
  | "Maintainability"
  | "Modifiability"
  | "Observability"
  | "Performance"
  | "Predictability"
  | "Privacy"
  | "Reliability"
  | "Safety"
  | "Scalability"
  | "Security"
  | "Usability";

export type QualityImpact = {
  attribute: QualityAttribute;
  explanation: string;
};

export type SequenceMessage = {
  from: number;
  to: number;
  label: string;
  reply?: boolean;
};

export type PatternSequence = {
  participants: string[];
  messages: SequenceMessage[];
};

export type Pattern = {
  id: string;
  number: string;
  name: string;
  category: PatternCategory;
  complexity: "Beginner" | "Intermediate" | "Advanced";
  summary: string;
  context: string;
  problem: string;
  solution: string;
  useWhen: string[];
  tradeoff: string;
  qualityAttributes: QualityAttribute[];
  benefits: QualityImpact[];
  liabilities: QualityImpact[];
  sequence: PatternSequence;
  calls: string;
  tools: boolean;
  files: number;
  flow: string[];
  code: {
    path: string;
    snippet: string;
  };
};

type PatternDraft = Omit<Pattern, "qualityAttributes" | "benefits" | "liabilities" | "sequence">;

const patternDrafts: PatternDraft[] = [
  {
    id: "passive-goal-creator",
    number: "01",
    name: "Passive Goal Creator",
    category: "Single agent",
    complexity: "Beginner",
    summary: "Turn one broad goal into sub-tasks, solve them, and synthesize a final response.",
    context: "Users often express intent as a broad goal rather than a precise instruction. A useful agent must first give that goal structure.",
    problem: "A single direct prompt can produce shallow, poorly organized answers because the model has not made the hidden work explicit.",
    solution: "Use one LLM call to decompose the goal, then a second call to solve the structured sub-tasks and combine the results.",
    useWhen: ["The task is open-ended", "No external tools are needed", "A transparent first agent is useful"],
    tradeoff: "Simple and easy to inspect, but it cannot ground answers in live data or act on external systems.",
    calls: "2 LLM calls",
    tools: false,
    files: 1,
    flow: ["Goal", "Decompose", "Solve", "Answer"],
    code: {
      path: "Single_Agent_Pattern/patterns/p01_passive_goal_creator/agent.py",
      snippet: `def run(user_goal: str) -> dict:
    breakdown = generate_response(
        f"Break this goal into clear sub-tasks: {user_goal}"
    )
    final_output = generate_response(
        f"Goal: {user_goal}\nSub-tasks: {breakdown}\n"
        "Solve each sub-task and synthesize the result."
    )
    return {"breakdown": breakdown, "final_output": final_output}`,
    },
  },
  {
    id: "proactive-goal-creator",
    number: "02",
    name: "Proactive Goal Creator",
    category: "Single agent",
    complexity: "Beginner",
    summary: "Enrich a goal with relevant external and situational context before reasoning.",
    context: "The same request can mean different things depending on date, time, location, device, user state, prior activity, available resources, or an optional artifact such as an image.",
    problem: "A passive agent only sees the words in the prompt and misses readily available context that could materially improve its answer.",
    solution: "Identify the relevant context sources, gather only those signals, and combine them with the user's goal before planning or responding. Multimodal analysis is optional, not required.",
    useWhen: ["Time, location, or environment affects the answer", "User or system state can resolve ambiguity", "The agent can safely access relevant context"],
    tradeoff: "More relevant responses come at the cost of extra context collection and stronger privacy boundaries.",
    calls: "1–2 LLM calls",
    tools: false,
    files: 2,
    flow: ["Goal", "Gather context", "Enrich", "Answer"],
    code: {
      path: "Single_Agent_Pattern/patterns/p02_proactive_goal_creator/agent.py",
      snippet: `context = gather_relevant_context(
    request=user_prompt,
    sources=["time", "location", "device", "session", "artifacts"],
)

enriched_prompt = build_enriched_prompt(
    goal=user_prompt,
    relevant_context=context,
)
final_output = generate_response(enriched_prompt)`,
    },
  },
  {
    id: "prompt-optimizer",
    number: "03",
    name: "Prompt Optimizer",
    category: "Single agent",
    complexity: "Beginner",
    summary: "Improve a rough prompt before asking the model to do the real work.",
    context: "People naturally write short, ambiguous prompts, while models perform better with clear goals, constraints, and output expectations.",
    problem: "The quality ceiling is set by the original prompt, forcing the task model to infer both what the user means and how to answer.",
    solution: "Add a dedicated optimization pass that rewrites the request, then execute the optimized version in a second call.",
    useWhen: ["Prompts are frequently vague", "Output structure matters", "A small latency increase is acceptable"],
    tradeoff: "Optimization adds latency and can accidentally shift intent, so the rewritten prompt should remain visible.",
    calls: "2 LLM calls",
    tools: false,
    files: 2,
    flow: ["Rough prompt", "Optimize", "Execute", "Response"],
    code: {
      path: "Single_Agent_Pattern/patterns/p03_prompt_optimizer/agent.py",
      snippet: `def run(user_prompt: str) -> dict:
    optimized_prompt = optimize(user_prompt)
    final_output = generate_response(optimized_prompt)

    return {
        "original_prompt": user_prompt,
        "optimized_prompt": optimized_prompt,
        "final_output": final_output,
    }`,
    },
  },
  {
    id: "rag",
    number: "04",
    name: "Retrieval-Augmented Generation",
    category: "Single agent",
    complexity: "Intermediate",
    summary: "Retrieve relevant knowledge and ground the model’s answer in it.",
    context: "Useful answers often depend on private, recent, or domain-specific material that is not reliably encoded in model weights.",
    problem: "Without evidence, an LLM may hallucinate, miss local facts, or answer from outdated training knowledge.",
    solution: "Search a knowledge base for relevant chunks, place them beside the question, and instruct the model to ground its answer in the retrieved context.",
    useWhen: ["Answers depend on a document corpus", "Citations or provenance matter", "Knowledge changes independently of the model"],
    tradeoff: "Answer quality now depends on retrieval quality, chunking, and context-window budget.",
    calls: "1 LLM call",
    tools: true,
    files: 2,
    flow: ["Question", "Retrieve", "Augment", "Grounded answer"],
    code: {
      path: "Single_Agent_Pattern/patterns/p04_rag/agent.py",
      snippet: `chunks = retrieve(user_query, top_k=top_k)
context_block = "\n\n".join(
    f"[{index + 1}] {chunk['title']}\n{chunk['content']}"
    for index, chunk in enumerate(chunks)
)
augmented_prompt = f"{context_block}\n\nQuestion: {user_query}"
final_output = generate_response(augmented_prompt)`,
    },
  },
  {
    id: "one-step-tool-agent",
    number: "05",
    name: "One-Step Tool Agent",
    category: "Single agent",
    complexity: "Intermediate",
    summary: "Plan and select one tool in a single structured model call.",
    context: "Many tasks need one deterministic capability—calculation, lookup, or text analysis—before an answer can be trusted.",
    problem: "Free-form model output is difficult to execute, while a long reasoning loop is unnecessary for straightforward tool use.",
    solution: "Ask the model for a plan, tool name, and parameters as JSON; execute the tool; then synthesize the result in a final call.",
    useWhen: ["One tool is sufficient", "Latency matters", "Tool schemas are simple and stable"],
    tradeoff: "Fast and compact, but planning and tool choice cannot correct one another before execution.",
    calls: "2 LLM calls",
    tools: true,
    files: 1,
    flow: ["Goal", "Plan + choose", "Tool", "Synthesize"],
    code: {
      path: "Single_Agent_Pattern/patterns/p05_one_step_tool_agent/agent.py",
      snippet: `raw = generate_response(planning_prompt)
parsed = _extract_json(raw)

selected_tool = parsed.get("selected_tool", "none")
parameters = parsed.get("parameters", {})
tool_output = execute_tool(selected_tool, parameters)

final_output = generate_response(
    f"Goal: {user_goal}\nTool output: {tool_output}"
)`,
    },
  },
  {
    id: "incremental-tool-agent",
    number: "06",
    name: "Incremental Tool Agent",
    category: "Single agent",
    complexity: "Intermediate",
    summary: "Separate analysis, tool choice, and parameter construction into deliberate rounds.",
    context: "High-consequence tool calls benefit from making each decision explicit and giving later decisions access to earlier reasoning.",
    problem: "Selecting a tool and constructing its parameters in one shot can hide ambiguity and produce brittle calls.",
    solution: "Use sequential calls for goal analysis, action planning, and exact parameters; execute only after all three stages agree.",
    useWhen: ["Tool calls need careful parameters", "Intermediate reasoning should be inspectable", "Reliability matters more than latency"],
    tradeoff: "More controllable than one-step selection, but significantly slower and more expensive.",
    calls: "4 LLM calls",
    tools: true,
    files: 1,
    flow: ["Analyze", "Choose", "Parameterize", "Execute"],
    code: {
      path: "Single_Agent_Pattern/patterns/p06_incremental_tool_agent/agent.py",
      snippet: `analysis = generate_response(analysis_prompt)
plan = generate_response(
    f"Goal: {user_goal}\nAnalysis: {analysis}\nChoose a tool."
)
spec_text = generate_response(
    f"Goal: {user_goal}\nAnalysis: {analysis}\nPlan: {plan}\n"
    "Return exact tool parameters as JSON."
)
spec = _extract_json(spec_text)
tool_output = execute_tool(spec["selected_tool"], spec["parameters"])`,
    },
  },
  {
    id: "single-path-plan",
    number: "07",
    name: "Single-Path Planning",
    category: "Single agent",
    complexity: "Advanced",
    summary: "Generate one linear plan, execute it step by step, and synthesize the trace.",
    context: "Complex goals need multiple dependent steps where each result informs what comes next.",
    problem: "A monolithic response cannot reliably manage dependencies, tool use, and accumulated intermediate results.",
    solution: "Create a four-to-six-step ordered plan, execute each step with shared accumulated context, then synthesize all outputs.",
    useWhen: ["The workflow is naturally sequential", "Steps depend on previous outputs", "One reasonable path is enough"],
    tradeoff: "Easy to follow, but an early planning mistake propagates through the entire execution.",
    calls: "2N + 2 calls",
    tools: true,
    files: 3,
    flow: ["Plan", "Step 1", "Step N", "Synthesize"],
    code: {
      path: "Single_Agent_Pattern/patterns/p07_single_path_plan/agent.py",
      snippet: `plan_steps = create_plan(user_goal)
step_outputs = []
accumulated_context = ""

for step in plan_steps:
    result = execute_step(
        user_goal, step["step_number"],
        step["description"], accumulated_context
    )
    step_outputs.append(result)
    accumulated_context += result["output"]`,
    },
  },
  {
    id: "multi-path-plan",
    number: "08",
    name: "Multi-Path Planning",
    category: "Single agent",
    complexity: "Advanced",
    summary: "Generate alternatives at each step and evaluate the best route before acting.",
    context: "For ambiguous or strategic tasks, there may be several plausible approaches and no single plan is obviously best upfront.",
    problem: "Committing to the first generated plan creates path dependence and misses stronger alternatives.",
    solution: "Generate two or three options per step, evaluate them against the goal and current context, then execute only the selected path.",
    useWhen: ["Several strategies are plausible", "Decision quality matters", "The extra evaluation cost is justified"],
    tradeoff: "Explores more of the solution space, but multiplies calls, latency, and opportunities for evaluator bias.",
    calls: "4N + 2 calls",
    tools: true,
    files: 4,
    flow: ["Branch", "Evaluate", "Choose", "Execute"],
    code: {
      path: "Single_Agent_Pattern/patterns/p08_multi_path_plan/agent.py",
      snippet: `for step in plan_steps:
    evaluation = evaluate_options(
        user_goal, step["step_number"],
        step["goal"], step["options"], accumulated_context
    )
    chosen = evaluation["chosen_option_id"]
    result = execute_step(
        user_goal, step["step_number"], step["goal"],
        evaluation["approach"], chosen, accumulated_context
    )`,
    },
  },
  {
    id: "self-reflection",
    number: "09",
    name: "Self-Reflection",
    category: "Single agent",
    complexity: "Advanced",
    summary: "Critique and revise a plan before any real action is taken.",
    context: "Agents frequently make plausible but flawed plans, especially when tools, constraints, or long chains of reasoning are involved.",
    problem: "Executing immediately gives the model no chance to detect mismatched tools, missing steps, or weak assumptions.",
    solution: "Insert a reflection pass between planning and execution; inspect the critique and execute the revised plan rather than the draft.",
    useWhen: ["Actions are costly", "Plans have several moving parts", "A short internal review can catch mistakes"],
    tradeoff: "Reflection improves many plans but can also overthink sound choices or reinforce the model’s original blind spots.",
    calls: "3N + 2 calls",
    tools: true,
    files: 4,
    flow: ["Plan", "Reflect", "Revise", "Execute"],
    code: {
      path: "Single_Agent_Pattern/patterns/p09_self_reflection/agent.py",
      snippet: `initial_plan = create_plan(user_goal)
reflection = reflect(user_goal, initial_plan)
final_plan = reflection["revised_steps"]

for step in final_plan:
    result = execute_step(user_goal, step, accumulated_context)
    step_outputs.append(result)

final_output = synthesize(step_outputs)`,
    },
  },
  {
    id: "voting-cooperation",
    number: "01",
    name: "Voting-Based Cooperation",
    category: "Multi-agent",
    complexity: "Intermediate",
    summary: "Ask diverse agents independently, then aggregate their votes into one decision.",
    context: "Independent perspectives can reduce the chance that one model persona or reasoning path dominates the result.",
    problem: "A single agent may be confidently wrong, but simply collecting multiple answers still leaves the user to reconcile them.",
    solution: "Run several voters on the same task and use majority, weighted scoring, or an LLM judge to select or merge the result.",
    useWhen: ["Independent judgment is valuable", "The task has a decision outcome", "Diverse personas or models are available"],
    tradeoff: "Ensembles reduce individual error but can converge on shared bias and cost N times as much.",
    calls: "N + 1–2 calls",
    tools: false,
    files: 5,
    flow: ["Question", "N voters", "Aggregate", "Decision"],
    code: {
      path: "Multi_Agent_Pattern/patterns/p01_voting_cooperation/agent.py",
      snippet: `votes = [agent.run(task) for agent in AGENTS]

result = aggregate(
    task=task,
    votes=votes,
    strategy=aggregation_mode,
    weights=agent_weights,
)

return {"votes": votes, "final_answer": result}`,
    },
  },
  {
    id: "role-based-cooperation",
    number: "02",
    name: "Role-Based Cooperation",
    category: "Multi-agent",
    complexity: "Advanced",
    summary: "Divide work among specialists and pass artifacts through explicit handoffs.",
    context: "Many real tasks cross product, architecture, implementation, and quality disciplines rather than fitting one generalist role.",
    problem: "One agent must juggle conflicting perspectives and often produces shallow coverage of each discipline.",
    solution: "Let an orchestrator assign scoped sub-tasks to specialist agents, then pass shared memory through a sequential team pipeline.",
    useWhen: ["The task spans distinct disciplines", "Handoffs mirror the real workflow", "Role accountability matters"],
    tradeoff: "Specialization improves depth but sequential handoffs increase latency and can amplify a bad early artifact.",
    calls: "1 + N + 1 calls",
    tools: false,
    files: 6,
    flow: ["Orchestrate", "PM", "Architect", "Build + QA"],
    code: {
      path: "Multi_Agent_Pattern/patterns/p02_role_based_cooperation/agent.py",
      snippet: `assignments = ORCHESTRATOR.divide(task, PIPELINE)
shared_memory = {}

for agent in PIPELINE:
    output = agent.execute(
        assignments[agent.role],
        shared_memory=shared_memory,
    )
    shared_memory[agent.role] = output

return synthesize(task, shared_memory)`,
    },
  },
  {
    id: "debate-cooperation",
    number: "03",
    name: "Debate-Based Cooperation",
    category: "Multi-agent",
    complexity: "Advanced",
    summary: "Let contrasting agents challenge one another before a neutral judge decides.",
    context: "Hard questions contain competing values and assumptions that become clearer through structured disagreement.",
    problem: "Independent answers never confront one another, so weak claims and hidden trade-offs can survive aggregation.",
    solution: "Run multiple debate rounds where each persona reads the transcript and responds directly, then ask a judge for a structured verdict.",
    useWhen: ["Trade-offs are genuinely contested", "Reasoning quality matters more than speed", "A transcript is useful evidence"],
    tradeoff: "Debate surfaces assumptions, but it is token-heavy and persuasive rhetoric can outweigh truth.",
    calls: "N × K + 1 calls",
    tools: false,
    files: 6,
    flow: ["Positions", "Debate K rounds", "Judge", "Verdict"],
    code: {
      path: "Multi_Agent_Pattern/patterns/p03_debate_cooperation/agent.py",
      snippet: `transcript = run_debate(
    topic=topic,
    debaters=DEBATERS,
    rounds=rounds,
)

verdict = JUDGE.decide(
    topic=topic,
    transcript=transcript,
)
return {"transcript": transcript, "verdict": verdict}`,
    },
  },
  {
    id: "registry-adapter",
    number: "04",
    name: "Registry & Adapter",
    category: "Multi-agent",
    complexity: "Advanced",
    summary: "Decouple discovery from execution with typed registries and one uniform adapter.",
    context: "Agent systems grow to include many specialists and deterministic tools that evolve independently.",
    problem: "Hard-coded routing couples the orchestrator to every implementation, making each new capability a system-wide change.",
    solution: "Register agents and tools separately, let a coordinator plan from their descriptions, and execute all targets through a shared adapter interface.",
    useWhen: ["Capabilities change frequently", "Agents and tools share a workflow", "Plugin-style extensibility is needed"],
    tradeoff: "Highly extensible, but schemas, registration quality, and adapter errors become critical infrastructure concerns.",
    calls: "1 + N + 1 calls",
    tools: true,
    files: 10,
    flow: ["Catalogs", "Coordinator", "Adapter", "Capability"],
    code: {
      path: "Multi_Agent_Pattern/patterns/p04_registry_adapter/orchestrator.py",
      snippet: `plan = coordinator.create_plan(
    task,
    agents=agent_registry.describe(),
    tools=tool_registry.describe(),
)

results = []
for step in plan["steps"]:
    results.append(adapter.execute(step["target"], step["input"]))

return coordinator.synthesize(task, results)`,
    },
  },
  {
    id: "parallel-fanout",
    number: "05",
    name: "Parallel Fan-Out",
    category: "Multi-agent",
    complexity: "Advanced",
    summary: "Decompose independent work, execute specialists concurrently, then merge.",
    context: "A complex task often contains branches that do not depend on one another and can be explored at the same time.",
    problem: "Sequential execution wastes time and forces every sub-task through one context window.",
    solution: "Use an initiator to create independent branches, run fixed specialist agents in parallel, and synthesize by merge, summary, or vote.",
    useWhen: ["Sub-tasks are independent", "Latency matters", "Specialist roles are known ahead of time"],
    tradeoff: "Wall time approaches the slowest branch, but parallel outputs may overlap or contradict one another.",
    calls: "1 + N + 1 calls",
    tools: false,
    files: 7,
    flow: ["Decompose", "Fan out", "Parallel work", "Merge"],
    code: {
      path: "Multi_Agent_Pattern/patterns/p05_parallel_fanout/agent.py",
      snippet: `subtasks = INITIATOR.decompose(task, len(SPECIALIST_AGENTS))

with ThreadPoolExecutor() as pool:
    futures = [
        pool.submit(agent.execute, subtask)
        for agent, subtask in zip(SPECIALIST_AGENTS, subtasks)
    ]
    outputs = [future.result() for future in futures]

return SYNTHESISER.combine(task, outputs, mode)`,
    },
  },
  {
    id: "hierarchical-decomposition",
    number: "06",
    name: "Hierarchical Decomposition",
    category: "Multi-agent",
    complexity: "Advanced",
    summary: "Recursively break deep problems into domains, sub-tasks, and worker jobs.",
    context: "Deep research and large programs are too broad for one planner to decompose well in a single pass.",
    problem: "A flat plan either stays vague or produces too many low-level tasks for one coordinator to manage coherently.",
    solution: "Use root, mid-level, and worker agents; each level decomposes only its scope and writes findings to shared hierarchy memory.",
    useWhen: ["The problem has natural levels", "Research depth matters", "Many workers need a shared scratchpad"],
    tradeoff: "Scales conceptual depth, but coordination overhead and compounded synthesis errors are substantial.",
    calls: "Root + branches + workers",
    tools: true,
    files: 6,
    flow: ["Root", "Domains", "Workers", "Shared memory"],
    code: {
      path: "Multi_Agent_Pattern/patterns/p06_hierarchical_decomposition/agent.py",
      snippet: `domains = ROOT_AGENT.decompose(task)

for domain in domains:
    mid_agent = MidLevelAgent(domain, memory)
    worker_specs = mid_agent.decompose()

    for spec in worker_specs:
        worker = WorkerAgent(spec, TOOL_POOL, memory)
        worker.execute()

return ROOT_AGENT.synthesize(memory)`,
    },
  },
  {
    id: "swarm",
    number: "07",
    name: "Swarm Choreography",
    category: "Multi-agent",
    complexity: "Advanced",
    summary: "Let peer agents choose who should act next until consensus emerges.",
    context: "Some creative and exploratory tasks benefit from fluid peer interaction rather than a rigid central plan.",
    problem: "A central orchestrator becomes a bottleneck and constrains which agent can respond to new information.",
    solution: "Use a dispatcher only to start; peers then share, critique, refine, and hand off directly until consensus or an iteration limit.",
    useWhen: ["The path should emerge dynamically", "Peers have complementary behaviors", "No fixed sequence is ideal"],
    tradeoff: "Flexible and resilient, but harder to predict, debug, terminate, and reproduce.",
    calls: "Dispatcher + N turns + synthesis",
    tools: false,
    files: 8,
    flow: ["Dispatch", "Peer message", "Peer handoff", "Consensus"],
    code: {
      path: "Multi_Agent_Pattern/patterns/p07_swarm/agent.py",
      snippet: `dispatch = DISPATCHER.select_first(task, SWARM_AGENTS)
engine = SwarmEngine(
    agents=SWARM_AGENTS,
    max_iterations=max_iterations,
)

result = engine.run(task, first_agent=dispatch["agent_id"])
final_answer = synthesize(task, result["history"])
return {**result, "final_answer": final_answer}`,
    },
  },
  {
    id: "human-in-the-loop",
    number: "08",
    name: "Human in the Loop",
    category: "Multi-agent",
    complexity: "Advanced",
    summary: "Pause irreversible or high-risk actions for explicit human approval.",
    context: "Agents in clinical, financial, and operations settings can propose actions whose consequences are difficult to reverse.",
    problem: "Fully autonomous execution treats routine and dangerous actions alike and leaves no accountable decision point.",
    solution: "Plan discrete actions, score risk, auto-run low and medium steps, and gate high-risk steps behind approval with a complete audit trail.",
    useWhen: ["Actions affect people or money", "Reversibility varies by step", "Auditability is required"],
    tradeoff: "Safer and accountable, but approvals interrupt flow and can become a throughput bottleneck.",
    calls: "Planner + N classifiers + executors",
    tools: false,
    files: 6,
    flow: ["Plan", "Classify risk", "Approve?", "Execute + audit"],
    code: {
      path: "Multi_Agent_Pattern/patterns/p08_human_in_the_loop/agent.py",
      snippet: `plan = plan_actions(task, domain, num_actions)

for action in plan["actions"]:
    risk = classify_action(action, domain, plan["task_summary"])
    if risk["approval_required"]:
        notifications = build_notifications(action, risk, domain)
    classified_actions.append({**action, **risk})

return execute_approved_plan(classified_actions, approvals)`,
    },
  },
  {
    id: "generator-critic",
    number: "09",
    name: "Generator–Critic Loop",
    category: "Multi-agent",
    complexity: "Intermediate",
    summary: "Iteratively draft, critique, and revise until a quality gate passes.",
    context: "Code, plans, and writing often improve through review against explicit criteria rather than one-shot generation.",
    problem: "A generator cannot reliably notice all of its own omissions, while a critique without revision does not improve the artifact.",
    solution: "Give generation and review to distinct agents; feed must-fix feedback into the next draft until the score threshold or iteration cap.",
    useWhen: ["Quality can be scored", "Revision is cheaper than failure", "Clear stopping criteria exist"],
    tradeoff: "Produces stronger drafts, but critics can cause endless churn without a strict budget and pass condition.",
    calls: "2 calls per iteration",
    tools: false,
    files: 3,
    flow: ["Generate", "Critique", "Revise", "Pass gate"],
    code: {
      path: "Multi_Agent_Pattern/patterns/p09_generator_critic/agent.py",
      snippet: `for iteration in range(1, max_iterations + 1):
    draft = GENERATOR.generate(
        task, previous_draft, critic_feedback
    )
    critique = CRITIC.critique(draft["draft"], task, draft_type)

    if critique["passed"]:
        break

    previous_draft = draft["draft"]
    critic_feedback = critique`,
    },
  },
  {
    id: "subagent-spawning",
    number: "10",
    name: "Sub-Agent Spawning",
    category: "Multi-agent",
    complexity: "Advanced",
    summary: "Invent specialist agents at runtime to match the task in front of you.",
    context: "Large migrations, document analysis, and system design need specialist roles that cannot always be known before seeing the task.",
    problem: "Fixed teams force every problem into predefined personas and may exceed one agent’s context window.",
    solution: "Let a spawner generate names, personas, and scopes dynamically; instantiate isolated sub-agents, run them in parallel, and synthesize.",
    useWhen: ["The right team depends on the task", "Context isolation helps", "Parallel specialization is valuable"],
    tradeoff: "Highly adaptive, but generated roles may overlap, omit a key specialty, or create unnecessary agents.",
    calls: "1 + N + 1 calls",
    tools: false,
    files: 4,
    flow: ["Analyze task", "Spawn roles", "Parallel agents", "Synthesize"],
    code: {
      path: "Multi_Agent_Pattern/patterns/p10_subagent_spawning/agent.py",
      snippet: `spawn_plan = SPAWNER.analyze_and_spawn(
    task, domain, max_subagents
)
subagents = [SubAgent(spec) for spec in spawn_plan["subagent_specs"]]

with ThreadPoolExecutor(max_workers=len(subagents)) as pool:
    results = list(pool.map(lambda agent: agent.execute_task(), subagents))

return synthesize(task, results, spawn_plan["synthesis_hint"])`,
    },
  },
  {
    id: "skill-library",
    number: "11",
    name: "Skill Library Evolution",
    category: "Multi-agent",
    complexity: "Intermediate",
    summary: "Persist reusable solutions so future sessions start with learned skills.",
    context: "Stateless agents repeatedly solve the same classes of problems from scratch, wasting time and tokens.",
    problem: "Conversation memory alone does not create a curated, searchable capability that can transfer across sessions.",
    solution: "Search a persistent skill store before solving, adapt relevant skills, and save reusable solutions with metadata and tags.",
    useWhen: ["Tasks recur across sessions", "Solutions can be generalized", "A growing local capability base is useful"],
    tradeoff: "Compounds useful knowledge, but stale or low-quality skills can also compound errors without curation.",
    calls: "Search + 1 solver call",
    tools: false,
    files: 4,
    flow: ["Search skills", "Adapt", "Solve", "Save skill"],
    code: {
      path: "Multi_Agent_Pattern/patterns/p11_skill_library/agent.py",
      snippet: `matches = STORE.search(task, top_k=3)
result = SKILL_AGENT.solve(task, relevant_skills=matches)

if result["is_reusable"]:
    skill = make_skill(
        name=result["skill_name"],
        description=result["skill_description"],
        solution=result["solution"],
        tags=result["tags"],
    )
    STORE.add(skill)`,
    },
  },
  {
    id: "dual-llm-security",
    number: "12",
    name: "Dual-LLM Security",
    category: "Multi-agent",
    complexity: "Advanced",
    summary: "Separate untrusted content from the tool-enabled model with a hard trust boundary.",
    context: "Emails, pages, and documents may contain prompt injection that attempts to hijack an agent with real tools.",
    problem: "A single model that reads raw data and can act on systems gives malicious content a direct path to privileged execution.",
    solution: "Use a tool-less quarantined model to extract symbolic values, validate them in deterministic code, and send only clean primitives to a privileged model.",
    useWhen: ["Agents ingest untrusted content", "Tools have meaningful side effects", "Prompt injection is in scope"],
    tradeoff: "Creates a strong boundary, but extraction schemas and deterministic validators must cover every allowed action.",
    calls: "2 LLM calls",
    tools: true,
    files: 5,
    flow: ["Untrusted data", "Quarantine", "Validate", "Privileged action"],
    code: {
      path: "Multi_Agent_Pattern/patterns/p12_dual_llm/agent.py",
      snippet: `extracted = QUARANTINED_LLM.extract(
    raw_data, task_context, action_type
)

validated = validate_and_substitute(
    extracted["template"], extracted["variables"]
)

if not validated["blocked"]:
    return PRIVILEGED_LLM.execute(
        action_type, validated["clean_parameters"]
    )`,
    },
  },
  {
    id: "core-memory",
    number: "01",
    name: "Core Memory",
    category: "Memory",
    complexity: "Beginner",
    summary: "Keep compact user, persona, and task facts always visible in context.",
    context: "An ongoing assistant needs a small set of identity and preference facts on every turn.",
    problem: "Conversation history grows beyond the context window, while re-retrieving essential facts on every message is wasteful.",
    solution: "Maintain editable memory blocks—human, persona, tasks—inside the active context and let the agent update them as facts change.",
    useWhen: ["A stable user profile matters", "The same facts are needed every turn", "Memory must remain inspectable"],
    tradeoff: "Always available and fast, but limited context space means every stored fact must earn its place.",
    calls: "Agent-managed",
    tools: true,
    files: 1,
    flow: ["Conversation", "Memory block", "Context window", "Response"],
    code: {
      path: "Memory_Pattern/memgpt_demo/01_core_memory.py",
      snippet: `agent = client.agents.create(
    name="core-memory-demo",
    memory_blocks=[
        CreateBlock(label="human", value="Name: Alex"),
        CreateBlock(label="persona", value="Helpful research assistant"),
        CreateBlock(label="tasks", value="Current goals: none"),
    ],
)

client.agents.messages.create(agent_id=agent.id, messages=[message])`,
    },
  },
  {
    id: "archival-memory",
    number: "02",
    name: "Archival Memory",
    category: "Memory",
    complexity: "Intermediate",
    summary: "Store an effectively unbounded fact base outside the context window.",
    context: "Long-lived agents accumulate more knowledge than can remain in active memory.",
    problem: "Keeping everything in context is expensive and eventually impossible; dropping old facts loses useful long-term knowledge.",
    solution: "Move durable facts into archival storage and expose semantic insert and search tools so the agent retrieves only what it needs.",
    useWhen: ["Facts accumulate over months", "Semantic retrieval is acceptable", "Long-term persistence matters"],
    tradeoff: "Scales far beyond context, but retrieval can miss relevant facts or return misleading neighbors.",
    calls: "Search on demand",
    tools: true,
    files: 1,
    flow: ["Fact", "Archive", "Semantic search", "Recall into context"],
    code: {
      path: "Memory_Pattern/memgpt_demo/02_archival_memory.py",
      snippet: `client.agents.passages.create(
    agent_id=agent.id,
    text="The user prefers concise technical explanations.",
)

results = client.agents.passages.search(
    agent_id=agent.id,
    query="How should explanations be written?",
)`,
    },
  },
  {
    id: "recall-memory",
    number: "03",
    name: "Recall Memory",
    category: "Memory",
    complexity: "Intermediate",
    summary: "Search the complete conversation history when old exchanges become relevant.",
    context: "Users refer back to decisions, promises, and details from conversations that are no longer in the recent message buffer.",
    problem: "A truncated context window makes the agent appear forgetful even when the full transcript still exists.",
    solution: "Persist every message in recall storage and let the agent search historical conversation records on demand.",
    useWhen: ["Conversation continuity matters", "Users reference prior sessions", "Exact historical wording may matter"],
    tradeoff: "Preserves the record, but searching a long conversation history adds latency and can surface stale intent.",
    calls: "Search on demand",
    tools: true,
    files: 1,
    flow: ["Messages", "Recall store", "Search history", "Continue"],
    code: {
      path: "Memory_Pattern/memgpt_demo/03_recall_memory.py",
      snippet: `for message in conversation:
    client.agents.messages.create(
        agent_id=agent.id,
        messages=[MessageCreate(role="user", content=message)],
    )

response = client.agents.messages.create(
    agent_id=agent.id,
    messages=[MessageCreate(
        role="user",
        content="What did we decide about the launch date?",
    )],
)`,
    },
  },
  {
    id: "scratchpad-memory",
    number: "04",
    name: "Scratchpad Memory",
    category: "Memory",
    complexity: "Beginner",
    summary: "Give the agent a durable working-notes block for intermediate state.",
    context: "Multi-step work produces partial results, hypotheses, and pending questions that are not user profile facts.",
    problem: "Keeping work-in-progress only in messages makes it noisy, fragile, and difficult for the agent to update cleanly.",
    solution: "Add a dedicated scratchpad block to core memory and let the agent append, replace, or clear notes as work evolves.",
    useWhen: ["Tasks span many turns", "Intermediate state matters", "Working notes should stay separate from identity"],
    tradeoff: "Makes state explicit, but unmanaged notes consume context and can preserve obsolete assumptions.",
    calls: "Agent-managed",
    tools: true,
    files: 1,
    flow: ["Work", "Scratchpad", "Update notes", "Resume"],
    code: {
      path: "Memory_Pattern/memgpt_demo/04_scratchpad.py",
      snippet: `scratchpad = CreateBlock(
    label="scratchpad",
    value="Working notes:\n- No active investigation",
    limit=2000,
)

agent = client.agents.create(
    name="scratchpad-demo",
    memory_blocks=[human, persona, scratchpad],
)`,
    },
  },
  {
    id: "shared-memory",
    number: "05",
    name: "Shared Memory",
    category: "Memory",
    complexity: "Advanced",
    summary: "Let multiple agents coordinate through one shared memory block.",
    context: "Specialist agents may work in separate contexts but still need a common source of truth for goals, progress, and handoffs.",
    problem: "Copying messages between agents duplicates context and creates inconsistent versions of shared state.",
    solution: "Attach the same mutable memory block to multiple agents so updates by one specialist are immediately available to the others.",
    useWhen: ["Agents share a project state", "Contexts should remain isolated", "A common task board is useful"],
    tradeoff: "Reduces duplication, but concurrent updates need clear ownership to avoid overwrites and coordination races.",
    calls: "Multi-agent managed",
    tools: true,
    files: 1,
    flow: ["Agent A", "Shared block", "Agent B", "Coordinated state"],
    code: {
      path: "Memory_Pattern/memgpt_demo/05_shared_memory_agents.py",
      snippet: `shared_tasks = client.blocks.create(
    label="shared_tasks",
    value="Project tasks and status",
)

researcher = client.agents.create(
    name="researcher", block_ids=[shared_tasks.id]
)
writer = client.agents.create(
    name="writer", block_ids=[shared_tasks.id]
)`,
    },
  },
];

type QualityProfile = Pick<Pattern, "problem" | "qualityAttributes" | "benefits" | "liabilities">;

const qualityProfiles: Record<string, QualityProfile> = {
  "passive-goal-creator": {
    problem: "Reliability, predictability, and usability are at risk when an ambiguous user goal is sent directly to a model: hidden sub-tasks remain unstated, yet the system must preserve the user's intent without inventing environmental context.",
    qualityAttributes: ["Reliability", "Predictability", "Usability", "Maintainability"],
    benefits: [
      { attribute: "Predictability", explanation: "Explicit sub-goals bound the work and make the path from intent to answer easier to anticipate." },
      { attribute: "Auditability", explanation: "The visible decomposition creates a trace from the original request to the final synthesis." },
      { attribute: "Maintainability", explanation: "A small, linear workflow is straightforward to implement, test, and debug." },
      { attribute: "Usability", explanation: "The user remains in control because the agent acts only on the context supplied in the dialogue." },
    ],
    liabilities: [
      { attribute: "Reliability", explanation: "Ambiguous wording can be decomposed incorrectly and propagate error through every sub-task." },
      { attribute: "Accuracy", explanation: "Missing environmental or multimodal context limits how precisely the agent can interpret the goal." },
      { attribute: "Adaptability", explanation: "The bounded workflow cannot independently inspect the environment or revise its objective." },
    ],
  },
  "proactive-goal-creator": {
    problem: "Accuracy, usability, and accessibility improve when the agent can infer missing context, but collecting external and situational signals—such as time, location, user state, system state, or optional multimodal input—introduces latency, cost, privacy, and maintainability pressure.",
    qualityAttributes: ["Accuracy", "Usability", "Accessibility", "Latency", "Cost", "Privacy"],
    benefits: [
      { attribute: "Accuracy", explanation: "Relevant signals such as time, location, session state, available resources, or optional artifacts reduce ambiguity and better ground the user's intent." },
      { attribute: "Usability", explanation: "Users provide less exhaustive prompting because the agent can inspect relevant surrounding context." },
      { attribute: "Adaptability", explanation: "The agent can tailor its goal and response to the current time, location, device, session, environment, or artifact." },
    ],
    liabilities: [
      { attribute: "Latency", explanation: "Context acquisition and any optional interpretation step add work before goal execution can begin." },
      { attribute: "Cost", explanation: "Additional model calls, tokens, sensors, or tool invocations increase per-request expense." },
      { attribute: "Privacy", explanation: "Inspecting local or personal context expands the data boundary and requires explicit consent and minimization." },
      { attribute: "Maintainability", explanation: "Every context source adds an integration that can drift, fail, or require platform-specific handling." },
    ],
  },
  "prompt-optimizer": {
    problem: "Reliability and interoperability suffer when prompts are vague or inconsistent, but a normalization stage must improve adherence without adding excessive latency, token cost, maintenance burden, or loss of useful creativity.",
    qualityAttributes: ["Reliability", "Interoperability", "Maintainability", "Latency", "Cost"],
    benefits: [
      { attribute: "Reliability", explanation: "Templates and examples make constraints and output expectations explicit, improving instruction adherence." },
      { attribute: "Interoperability", explanation: "A standardized prompt contract gives downstream agents and tools a more consistent input shape." },
      { attribute: "Modifiability", explanation: "Domain-specific templates can be changed independently of the task agent's core implementation." },
    ],
    liabilities: [
      { attribute: "Maintainability", explanation: "Templates, examples, and model behavior can drift as requirements change, demanding continuous review." },
      { attribute: "Latency", explanation: "The optimization pass delays every task even when the original prompt was already sufficient." },
      { attribute: "Cost", explanation: "Rewriting and then executing the prompt consumes additional tokens and model calls." },
      { attribute: "Accuracy", explanation: "Over-optimization can subtly shift user intent or constrain creative responses that would have been useful." },
    ],
  },
  rag: {
    problem: "Reliability and data freshness require grounding answers in current organizational knowledge, while retrieval infrastructure must control latency, cost, privacy exposure, and ongoing index maintenance.",
    qualityAttributes: ["Reliability", "Data freshness", "Maintainability", "Latency", "Cost", "Privacy"],
    benefits: [
      { attribute: "Reliability", explanation: "Retrieved evidence constrains generation and reduces unsupported claims when relevant sources are found." },
      { attribute: "Data freshness", explanation: "Knowledge can be updated in the corpus without retraining or replacing the model." },
      { attribute: "Modifiability", explanation: "Documents, chunking, ranking, and generation can evolve as separable architectural elements." },
      { attribute: "Cost", explanation: "Updating a retrieval corpus is often less expensive than repeated fine-tuning for changing knowledge." },
      { attribute: "Privacy", explanation: "Sensitive knowledge can remain in a controlled store rather than being embedded into shared model weights." },
    ],
    liabilities: [
      { attribute: "Latency", explanation: "Embedding, search, reranking, and larger prompts add response time to each grounded query." },
      { attribute: "Maintainability", explanation: "Ingestion, chunking, embeddings, access controls, and index lifecycle create an operational pipeline." },
      { attribute: "Reliability", explanation: "Poor recall, irrelevant chunks, or weak source data can still yield confidently incorrect answers." },
      { attribute: "Data freshness", explanation: "Freshness becomes an explicit synchronization obligation rather than an automatic property." },
    ],
  },
  "one-step-tool-agent": {
    problem: "Latency and cost favor a compact tool-use path, while reliability, security, and observability require the chosen tool and parameters to be valid before execution.",
    qualityAttributes: ["Latency", "Cost", "Reliability", "Security", "Observability"],
    benefits: [
      { attribute: "Latency", explanation: "Planning and selection happen together, minimizing model round trips before execution." },
      { attribute: "Cost", explanation: "The short control loop uses fewer tokens and calls than iterative planning." },
      { attribute: "Performance", explanation: "For simple, well-bounded tasks, one query avoids orchestration that would not improve the result." },
      { attribute: "Maintainability", explanation: "A small orchestration surface is easy to understand for stable, narrow tool sets." },
    ],
    liabilities: [
      { attribute: "Reliability", explanation: "An early planning mistake reaches execution without an intermediate correction point." },
      { attribute: "Accuracy", explanation: "One-step querying does not fit every scenario; limited context can lower the quality of complex decisions." },
      { attribute: "Security", explanation: "Parameter validation and permission checks must compensate for the compressed decision process." },
      { attribute: "Observability", explanation: "Fewer explicit stages provide less evidence for diagnosing why a tool was selected." },
    ],
  },
  "incremental-tool-agent": {
    problem: "Reliability, safety, and observability demand deliberate tool decisions, but separating analysis, selection, and parameterization increases latency, cost, and orchestration complexity.",
    qualityAttributes: ["Reliability", "Safety", "Observability", "Latency", "Cost"],
    benefits: [
      { attribute: "Reliability", explanation: "Later stages can validate earlier reasoning before a side effect occurs." },
      { attribute: "Accuracy", explanation: "Incremental exchanges support larger effective context and let later reasoning build on earlier results." },
      { attribute: "Observability", explanation: "Each decision leaves an inspectable artifact for debugging and evaluation." },
      { attribute: "Safety", explanation: "Explicit checkpoints create places to enforce schemas, permissions, and policy." },
    ],
    liabilities: [
      { attribute: "Latency", explanation: "Sequential model calls lengthen the critical path." },
      { attribute: "Cost", explanation: "Repeated reasoning and context transfer consume more tokens; uncontrolled back-and-forth can grow without a useful bound." },
      { attribute: "Maintainability", explanation: "More stages introduce more prompts, state transitions, and failure modes to maintain." },
    ],
  },
  "single-path-plan": {
    problem: "Predictability and observability require an explicit plan, while reliability and performance are threatened by sequential dependencies and the absence of alternative routes.",
    qualityAttributes: ["Predictability", "Observability", "Reliability", "Latency"],
    benefits: [
      { attribute: "Predictability", explanation: "A single ordered route makes execution behavior and resource use easier to forecast." },
      { attribute: "Performance", explanation: "Deterministic workflows execute efficiently because the agent does not generate or compare alternatives." },
      { attribute: "Observability", explanation: "Named steps expose progress and the point at which a run fails." },
      { attribute: "Maintainability", explanation: "The linear plan is simple to test and reason about." },
    ],
    liabilities: [
      { attribute: "Reliability", explanation: "One failed or incorrect step can invalidate every dependent step." },
      { attribute: "Latency", explanation: "Independent work may still execute sequentially on the critical path." },
      { attribute: "Usability", explanation: "Users have little opportunity to compare or influence alternatives once the single route is selected." },
      { attribute: "Adaptability", explanation: "The agent has no built-in alternative when assumptions change during execution." },
    ],
  },
  "multi-path-plan": {
    problem: "Reliability and decision accuracy benefit from exploring alternatives, but parallel candidates and evaluation add cost, latency, nondeterminism, and maintenance overhead.",
    qualityAttributes: ["Reliability", "Accuracy", "Cost", "Latency", "Maintainability"],
    benefits: [
      { attribute: "Reliability", explanation: "Alternative plans reduce dependence on one brittle reasoning path." },
      { attribute: "Accuracy", explanation: "Comparing candidates can surface stronger assumptions and more complete solutions." },
      { attribute: "Usability", explanation: "Users can inspect alternatives and participate in selecting the route that best fits their priorities." },
      { attribute: "Adaptability", explanation: "The system can select a route that better fits the observed situation." },
    ],
    liabilities: [
      { attribute: "Cost", explanation: "Generating and evaluating multiple plans multiplies inference work." },
      { attribute: "Latency", explanation: "Selection adds a decision stage even when candidates run concurrently." },
      { attribute: "Maintainability", explanation: "Branching, pruning, and evaluator prompts become critical orchestration components that require calibration." },
      { attribute: "Cost", explanation: "Excessive branching can multiply work without improving use cases that have one clear path." },
    ],
  },
  "self-reflection": {
    problem: "Accuracy and reliability require detecting defects before release, while repeated self-review can increase latency and cost without guaranteeing an independent judgment.",
    qualityAttributes: ["Accuracy", "Reliability", "Latency", "Cost", "Predictability"],
    benefits: [
      { attribute: "Reliability", explanation: "A critique-and-revise loop catches omissions and inconsistencies before the answer is returned." },
      { attribute: "Accuracy", explanation: "Explicit review encourages the model to test claims and improve completeness." },
      { attribute: "Auditability", explanation: "The critique exposes reasoning and creates evidence for why the plan changed." },
      { attribute: "Safety", explanation: "Reflection offers an additional policy and risk checkpoint." },
    ],
    liabilities: [
      { attribute: "Latency", explanation: "Every review round delays completion." },
      { attribute: "Cost", explanation: "Drafts, critiques, and revisions repeatedly consume context and inference." },
      { attribute: "Reliability", explanation: "The same model may preserve its original blind spots or introduce regressions while revising." },
      { attribute: "Maintainability", explanation: "Effective reflection prompts and stopping rules require domain expertise and continuous refinement." },
    ],
  },
  "voting-cooperation": {
    problem: "Reliability needs protection from a single agent's error, while independent votes increase latency and cost and only help when the voters provide genuinely diverse judgments.",
    qualityAttributes: ["Reliability", "Accuracy", "Cost", "Latency"],
    benefits: [
      { attribute: "Reliability", explanation: "A majority can mask isolated reasoning failures or unstable outputs." },
      { attribute: "Accuracy", explanation: "Independent perspectives improve decision quality when errors are not correlated." },
      { attribute: "Performance", explanation: "Voters are model-agnostic and can run in parallel before aggregation." },
      { attribute: "Maintainability", explanation: "The ensemble structure is comparatively easy to implement when votes have a clear schema." },
    ],
    liabilities: [
      { attribute: "Cost", explanation: "Every voter performs substantially duplicated work." },
      { attribute: "Latency", explanation: "The decision waits for the slowest required vote and aggregation." },
      { attribute: "Reliability", explanation: "Shared model biases can create confident consensus without correctness." },
      { attribute: "Accuracy", explanation: "Voting is a poor fit when several answers are valid or when the aggregator cannot judge nuanced outputs." },
    ],
  },
  "role-based-cooperation": {
    problem: "Maintainability and reliability improve when responsibilities are cohesive and explicit, but handoffs introduce coupling, latency, and cascading failure risk.",
    qualityAttributes: ["Maintainability", "Reliability", "Observability", "Latency"],
    benefits: [
      { attribute: "Maintainability", explanation: "Role boundaries localize prompts, tools, and changes to a focused responsibility." },
      { attribute: "Observability", explanation: "Named handoffs make ownership and intermediate artifacts visible." },
      { attribute: "Reliability", explanation: "Specialized instructions reduce the scope each agent must reason about." },
      { attribute: "Modifiability", explanation: "New roles and heterogeneous models can be introduced behind explicit responsibility boundaries." },
    ],
    liabilities: [
      { attribute: "Latency", explanation: "Sequential handoffs lengthen the end-to-end path." },
      { attribute: "Cost", explanation: "Adding roles increases model work, communication, and the number of components that can fail." },
      { attribute: "Reliability", explanation: "A malformed intermediate artifact can contaminate every downstream role." },
      { attribute: "Modifiability", explanation: "Changing one role's contract may require coordinated updates across the workflow." },
      { attribute: "Adaptability", explanation: "Rigidly predefined roles may handle unexpected tasks poorly when no specialist owns them." },
    ],
  },
  "debate-cooperation": {
    problem: "Decision reliability benefits from explicit challenge, while multiple argumentative rounds impose latency and cost and may reward persuasion rather than evidence.",
    qualityAttributes: ["Reliability", "Auditability", "Cost", "Latency"],
    benefits: [
      { attribute: "Reliability", explanation: "Opposing agents expose assumptions and counterexamples before a decision is accepted." },
      { attribute: "Accuracy", explanation: "Agents can revise positions when peers provide better evidence, improving factual decision quality." },
      { attribute: "Auditability", explanation: "Arguments create a visible record of competing evidence and rationale." },
    ],
    liabilities: [
      { attribute: "Latency", explanation: "Multi-round exchanges delay convergence." },
      { attribute: "Cost", explanation: "Each position, rebuttal, and judgment consumes additional inference." },
      { attribute: "Accuracy", explanation: "A persuasive but weak argument can dominate if the judge is poorly calibrated." },
      { attribute: "Scalability", explanation: "Communication grows quickly with more agents and debate rounds." },
      { attribute: "Predictability", explanation: "The agents may not converge, so round and termination limits must be explicit." },
    ],
  },
  "registry-adapter": {
    problem: "Interoperability and modifiability require agents to discover capabilities through stable contracts, while registry correctness, adapter maintenance, and extra indirection affect reliability and latency.",
    qualityAttributes: ["Interoperability", "Modifiability", "Maintainability", "Reliability"],
    benefits: [
      { attribute: "Interoperability", explanation: "Adapters normalize heterogeneous agents behind a common invocation contract." },
      { attribute: "Modifiability", explanation: "Agents can be added or replaced without rewriting every caller." },
      { attribute: "Maintainability", explanation: "Discovery metadata centralizes capability descriptions and routing rules." },
      { attribute: "Adaptability", explanation: "Version metadata and dynamic selection support controlled A/B testing of agents and tools." },
    ],
    liabilities: [
      { attribute: "Reliability", explanation: "Stale metadata or an unavailable registry can misroute or block requests." },
      { attribute: "Latency", explanation: "Discovery and adaptation add work before useful execution begins." },
      { attribute: "Maintainability", explanation: "Adapters and capability schemas must evolve with every connected system." },
      { attribute: "Security", explanation: "A compromised registry can advertise unsafe capabilities or redirect work to untrusted implementations." },
      { attribute: "Performance", explanation: "Cold-started or newly registered agents may respond slowly or remain under-selected until metadata improves." },
    ],
  },
  "parallel-fanout": {
    problem: "Performance and scalability favor concurrent specialist work, while cost, merge consistency, and downstream load must remain bounded.",
    qualityAttributes: ["Performance", "Scalability", "Cost", "Reliability"],
    benefits: [
      { attribute: "Performance", explanation: "Independent tasks complete concurrently, so ideal latency approaches the slowest branch rather than the sum of all branches." },
      { attribute: "Scalability", explanation: "Specialist capacity can scale independently for different task classes." },
      { attribute: "Reliability", explanation: "A failed branch can be retried or degraded without discarding all successful branches." },
    ],
    liabilities: [
      { attribute: "Cost", explanation: "Concurrency can create bursty inference and tool consumption." },
      { attribute: "Reliability", explanation: "Hidden dependencies and conflicting outputs violate the independence assumption and complicate synthesis." },
      { attribute: "Maintainability", explanation: "The synthesizer must reconcile heterogeneous formats, missing branches, and contradictory evidence." },
      { attribute: "Performance", explanation: "Unbounded fan-out can overload rate limits, queues, or downstream services." },
    ],
  },
  "hierarchical-decomposition": {
    problem: "Scalability and maintainability need large goals decomposed into cohesive subproblems, but deeper coordination increases latency, cost, and compounded error risk.",
    qualityAttributes: ["Scalability", "Maintainability", "Reliability", "Latency", "Cost"],
    benefits: [
      { attribute: "Scalability", explanation: "A coordinator delegates bounded subproblems that can execute independently." },
      { attribute: "Accuracy", explanation: "Multi-level decomposition helps agents reduce ambiguity before attempting open-ended work." },
      { attribute: "Maintainability", explanation: "Specialists keep tools and knowledge close to one domain responsibility." },
      { attribute: "Modifiability", explanation: "Subtrees can evolve without redesigning the complete system." },
    ],
    liabilities: [
      { attribute: "Reliability", explanation: "Incorrect decomposition propagates into many otherwise competent specialists." },
      { attribute: "Latency", explanation: "Coordination and synthesis add levels to the execution path." },
      { attribute: "Cost", explanation: "Management layers and repeated context transfer increase inference usage." },
      { attribute: "Observability", explanation: "Deep trees are difficult to debug because state and causality cross many delegation boundaries." },
      { attribute: "Maintainability", explanation: "Over-decomposition and context sharing across levels create substantial coordination complexity." },
    ],
  },
  swarm: {
    problem: "Adaptability and resilience favor decentralized agent behavior, while predictable termination, observability, security, and cost control become harder without central coordination.",
    qualityAttributes: ["Adaptability", "Reliability", "Predictability", "Observability", "Cost"],
    benefits: [
      { attribute: "Adaptability", explanation: "Agents can reorganize around emerging work without a fixed orchestration graph." },
      { attribute: "Reliability", explanation: "Decentralization avoids one coordinator becoming the sole point of failure." },
      { attribute: "Accuracy", explanation: "Peers can challenge and correct one another at any point, supporting creative multi-expert outcomes." },
      { attribute: "Scalability", explanation: "Capacity can grow by adding peers that follow the same interaction rules." },
    ],
    liabilities: [
      { attribute: "Predictability", explanation: "Emergent paths and termination behavior are difficult to bound." },
      { attribute: "Observability", explanation: "Distributed decisions make causal debugging and attribution difficult." },
      { attribute: "Cost", explanation: "Uncontrolled peer interactions can generate redundant work and message growth." },
      { attribute: "Maintainability", explanation: "All-to-all communication and distributed state make the mechanism substantially harder to implement." },
      { attribute: "Latency", explanation: "Peer interaction depth is dynamic, making completion time difficult to predict." },
    ],
  },
  "human-in-the-loop": {
    problem: "Safety, reliability, and accountability require human authority over consequential actions, while waiting for review reduces latency, availability, and throughput.",
    qualityAttributes: ["Safety", "Reliability", "Auditability", "Latency", "Cost"],
    benefits: [
      { attribute: "Safety", explanation: "A person can block harmful, irreversible, or policy-sensitive actions." },
      { attribute: "Reliability", explanation: "Human judgment handles ambiguity and edge cases outside the agent's competence." },
      { attribute: "Auditability", explanation: "Approval records establish accountable decision ownership." },
      { attribute: "Usability", explanation: "Human authority lets users contest high-impact decisions and build trust before delegating more." },
    ],
    liabilities: [
      { attribute: "Latency", explanation: "Execution pauses until a reviewer is available." },
      { attribute: "Cost", explanation: "Skilled review time can dominate operating expense at scale." },
      { attribute: "Scalability", explanation: "Human capacity becomes a throughput bottleneck during bursts." },
      { attribute: "Usability", explanation: "Too many interruptions create approval fatigue and encourage superficial review." },
      { attribute: "Reliability", explanation: "Defining risk boundaries incorrectly can either over-escalate routine work or miss dangerous actions." },
    ],
  },
  "generator-critic": {
    problem: "Accuracy and reliability benefit from an independent quality gate, while critic calls, revision loops, and evaluator maintenance add latency and cost.",
    qualityAttributes: ["Accuracy", "Reliability", "Latency", "Cost", "Maintainability"],
    benefits: [
      { attribute: "Accuracy", explanation: "A separate critic checks the artifact against explicit acceptance criteria." },
      { attribute: "Reliability", explanation: "Revision is triggered before weak output reaches the user or another system." },
      { attribute: "Observability", explanation: "Critiques make quality failures explicit and measurable." },
      { attribute: "Modifiability", explanation: "The same generator can be paired with domain-specific critics for security, correctness, or style." },
    ],
    liabilities: [
      { attribute: "Latency", explanation: "Generation, critique, and revision extend the critical path." },
      { attribute: "Cost", explanation: "Quality assurance requires additional model work on every iteration." },
      { attribute: "Maintainability", explanation: "Critic criteria and thresholds must track changing product expectations." },
      { attribute: "Accuracy", explanation: "Quality gains often saturate after a few rounds, while a passing critic still does not guarantee correctness." },
      { attribute: "Predictability", explanation: "Exit conditions must prevent infinite revision loops without accepting an inadequate artifact too early." },
    ],
  },
  "subagent-spawning": {
    problem: "Adaptability and scalability favor creating specialists on demand, while dynamic teams challenge cost control, predictability, security governance, and lifecycle management.",
    qualityAttributes: ["Adaptability", "Scalability", "Cost", "Predictability", "Security"],
    benefits: [
      { attribute: "Adaptability", explanation: "The system creates expertise and instructions that fit the current task rather than a fixed catalog." },
      { attribute: "Scalability", explanation: "Scoped sub-agents process work in parallel and let the system exceed one agent's context-window capacity." },
      { attribute: "Maintainability", explanation: "Temporary specialists isolate files and task context from the parent agent." },
    ],
    liabilities: [
      { attribute: "Cost", explanation: "The number and depth of spawned agents can grow unpredictably." },
      { attribute: "Security", explanation: "Dynamic agents require least-privilege tools, credentials, and data scopes." },
      { attribute: "Predictability", explanation: "Runtime topology and completion behavior vary by request." },
      { attribute: "Reliability", explanation: "Parallel edits can create merge conflicts and inconsistent decisions across sub-agents." },
      { attribute: "Cost", explanation: "Spawning, monitoring, and coordinating child agents adds overhead beyond their model calls." },
    ],
  },
  "skill-library": {
    problem: "Performance, consistency, and cost improve when successful procedures are reused, while stale or unsafe skills create reliability, security, and maintenance obligations.",
    qualityAttributes: ["Performance", "Cost", "Reliability", "Maintainability", "Security"],
    benefits: [
      { attribute: "Performance", explanation: "Known procedures reduce repeated planning and shorten time to action." },
      { attribute: "Cost", explanation: "Reusable skills avoid rediscovering the same workflow in every session." },
      { attribute: "Reliability", explanation: "Validated procedures make repeated behavior more consistent." },
      { attribute: "Adaptability", explanation: "The library lets behavior improve across sessions without retraining the underlying model." },
      { attribute: "Modifiability", explanation: "Small skills can be composed into richer capabilities instead of building each workflow from scratch." },
    ],
    liabilities: [
      { attribute: "Maintainability", explanation: "Skills need ownership, versioning, evaluation, and retirement as dependencies change." },
      { attribute: "Reliability", explanation: "A stale procedure can repeatedly produce the same systematic failure." },
      { attribute: "Security", explanation: "Imported or mutable skills expand the executable supply chain and trust boundary." },
      { attribute: "Latency", explanation: "Searching and ranking the library adds discovery overhead before execution." },
      { attribute: "Accuracy", explanation: "Without comparative evaluation, the system cannot know whether a stored skill is better than fresh generation." },
    ],
  },
  "dual-llm-security": {
    problem: "Security and privacy require isolating untrusted content from privileged actions, while the trust-boundary protocol adds latency, cost, availability dependencies, and schema maintenance.",
    qualityAttributes: ["Security", "Privacy", "Reliability", "Latency", "Cost"],
    benefits: [
      { attribute: "Security", explanation: "The privileged model never consumes raw untrusted content, reducing prompt-injection reach." },
      { attribute: "Privacy", explanation: "Data can be minimized or summarized before crossing into a more privileged context." },
      { attribute: "Auditability", explanation: "The structured handoff creates a clear boundary for validation and logging." },
      { attribute: "Maintainability", explanation: "Separating data interpretation from privileged action creates clear responsibilities and supports layered guardrails." },
    ],
    liabilities: [
      { attribute: "Latency", explanation: "Two model stages and validation increase end-to-end response time." },
      { attribute: "Cost", explanation: "Isolation duplicates inference and context handling." },
      { attribute: "Maintainability", explanation: "Symbolic substitution, schemas, and trust assumptions must evolve consistently on both sides of the boundary." },
      { attribute: "Modifiability", explanation: "Tasks that cannot be decomposed into validated primitives may not fit the trust-boundary design." },
    ],
  },
  "core-memory": {
    problem: "Usability and latency benefit from always-available personal context, while limited context capacity, privacy exposure, and stale facts threaten performance and reliability.",
    qualityAttributes: ["Usability", "Latency", "Privacy", "Reliability", "Maintainability"],
    benefits: [
      { attribute: "Usability", explanation: "Persistent identity and preferences support continuity without repeated explanation." },
      { attribute: "Latency", explanation: "Critical facts are immediately available without retrieval." },
      { attribute: "Reliability", explanation: "Stable instructions remain present throughout the interaction." },
    ],
    liabilities: [
      { attribute: "Cost", explanation: "Always-in-context memory consumes tokens on every turn." },
      { attribute: "Privacy", explanation: "Sensitive facts remain continuously exposed to the active agent context." },
      { attribute: "Reliability", explanation: "Outdated core facts can systematically bias every response." },
    ],
  },
  "archival-memory": {
    problem: "Scalability and cost require moving long-lived knowledge outside the active context, while retrieval latency, ranking quality, and corpus maintenance affect reliability and freshness.",
    qualityAttributes: ["Scalability", "Cost", "Latency", "Reliability", "Data freshness"],
    benefits: [
      { attribute: "Scalability", explanation: "Large histories and documents persist without consuming the active context window." },
      { attribute: "Cost", explanation: "Only selected records are injected into expensive model context." },
      { attribute: "Data freshness", explanation: "Stored knowledge can be updated independently of the model." },
    ],
    liabilities: [
      { attribute: "Latency", explanation: "Retrieval adds an access step before reasoning." },
      { attribute: "Reliability", explanation: "Poor ranking or missing metadata can hide the fact needed for the task." },
      { attribute: "Maintainability", explanation: "Storage, indexing, retention, and deletion policies require ongoing operation." },
    ],
  },
  "recall-memory": {
    problem: "Conversation continuity and auditability require searchable interaction history, while privacy, stale intent, retrieval latency, and retention rules must be controlled.",
    qualityAttributes: ["Usability", "Auditability", "Privacy", "Latency", "Data freshness"],
    benefits: [
      { attribute: "Usability", explanation: "The agent can resume prior decisions without asking the user to repeat them." },
      { attribute: "Auditability", explanation: "Past messages provide a chronological record of decisions and commitments." },
      { attribute: "Reliability", explanation: "Retrieved history helps preserve constraints established in earlier sessions." },
    ],
    liabilities: [
      { attribute: "Privacy", explanation: "Long-lived transcripts increase retention and access-control risk." },
      { attribute: "Latency", explanation: "Searching and injecting history adds processing to each relevant turn." },
      { attribute: "Data freshness", explanation: "Old preferences or superseded decisions can be mistaken for current intent." },
    ],
  },
  "scratchpad-memory": {
    problem: "Reliability and observability require durable intermediate state across long tasks, while context cost, stale assumptions, and accidental disclosure must remain bounded.",
    qualityAttributes: ["Reliability", "Observability", "Maintainability", "Cost", "Privacy"],
    benefits: [
      { attribute: "Reliability", explanation: "Explicit working state helps the agent resume without losing partial results or pending questions." },
      { attribute: "Observability", explanation: "Intermediate hypotheses and decisions are visible for debugging." },
      { attribute: "Maintainability", explanation: "Working notes stay separate from identity, conversation, and durable knowledge." },
    ],
    liabilities: [
      { attribute: "Cost", explanation: "Large notes consume active context and inference budget." },
      { attribute: "Reliability", explanation: "Obsolete assumptions can persist and steer later work incorrectly." },
      { attribute: "Privacy", explanation: "Unfiltered notes may capture sensitive details not intended for durable memory." },
    ],
  },
  "shared-memory": {
    problem: "Consistency and interoperability require multiple agents to share one source of truth, while concurrent mutation, broad access, coupling, and scale challenge reliability and security.",
    qualityAttributes: ["Reliability", "Interoperability", "Scalability", "Security", "Maintainability"],
    benefits: [
      { attribute: "Interoperability", explanation: "Agents coordinate through a common state contract rather than copying messages." },
      { attribute: "Reliability", explanation: "A shared source reduces divergent versions of goals, status, and handoff data." },
      { attribute: "Cost", explanation: "Common state avoids repeatedly duplicating the same context across agents." },
    ],
    liabilities: [
      { attribute: "Reliability", explanation: "Concurrent writes can overwrite work or expose partially updated state." },
      { attribute: "Security", explanation: "Shared access broadens the impact of an over-privileged or compromised agent." },
      { attribute: "Maintainability", explanation: "Schema changes and ownership rules couple all participating agents." },
    ],
  },
};

const sequenceProfiles: Record<string, PatternSequence> = {
  "passive-goal-creator": {
    participants: ["User", "Goal agent", "LLM"],
    messages: [
      { from: 0, to: 1, label: "Broad goal" },
      { from: 1, to: 2, label: "Decompose goal" },
      { from: 2, to: 1, label: "Structured sub-goals", reply: true },
      { from: 1, to: 2, label: "Solve and synthesize" },
      { from: 2, to: 1, label: "Final synthesis", reply: true },
      { from: 1, to: 0, label: "Structured response", reply: true },
    ],
  },
  "proactive-goal-creator": {
    participants: ["User", "Agent", "Context sources", "LLM"],
    messages: [
      { from: 0, to: 1, label: "Goal" },
      { from: 1, to: 2, label: "Request relevant context" },
      { from: 2, to: 1, label: "Time, location, state, artifacts", reply: true },
      { from: 1, to: 3, label: "Goal + selected context" },
      { from: 3, to: 1, label: "Context-aware result", reply: true },
      { from: 1, to: 0, label: "Context-aware answer", reply: true },
    ],
  },
  "prompt-optimizer": {
    participants: ["User", "Prompt optimizer", "Task LLM"],
    messages: [
      { from: 0, to: 1, label: "Rough prompt" },
      { from: 1, to: 2, label: "Optimized instructions" },
      { from: 2, to: 1, label: "Task result", reply: true },
      { from: 1, to: 0, label: "Result + visible rewrite", reply: true },
    ],
  },
  rag: {
    participants: ["User", "Agent", "Retriever", "Knowledge base", "LLM"],
    messages: [
      { from: 0, to: 1, label: "Question" },
      { from: 1, to: 2, label: "Semantic query" },
      { from: 2, to: 3, label: "Search top-k chunks" },
      { from: 3, to: 2, label: "Relevant evidence", reply: true },
      { from: 2, to: 1, label: "Ranked context", reply: true },
      { from: 1, to: 4, label: "Question + evidence" },
      { from: 4, to: 1, label: "Grounded answer", reply: true },
      { from: 1, to: 0, label: "Answer with provenance", reply: true },
    ],
  },
  "one-step-tool-agent": {
    participants: ["User", "Agent", "LLM", "Tool"],
    messages: [
      { from: 0, to: 1, label: "Goal" },
      { from: 1, to: 2, label: "Plan + choose tool" },
      { from: 2, to: 1, label: "Tool and parameters", reply: true },
      { from: 1, to: 3, label: "Execute once" },
      { from: 3, to: 1, label: "Tool result", reply: true },
      { from: 1, to: 0, label: "Synthesized response", reply: true },
    ],
  },
  "incremental-tool-agent": {
    participants: ["User", "Agent", "LLM", "Tool"],
    messages: [
      { from: 0, to: 1, label: "Goal" },
      { from: 1, to: 2, label: "Analyze goal" },
      { from: 2, to: 1, label: "Goal analysis", reply: true },
      { from: 1, to: 2, label: "Choose action" },
      { from: 2, to: 1, label: "Tool + exact parameters", reply: true },
      { from: 1, to: 3, label: "Validated execution" },
      { from: 3, to: 1, label: "Tool result", reply: true },
      { from: 1, to: 0, label: "Final response", reply: true },
    ],
  },
  "single-path-plan": {
    participants: ["User", "Planner", "Executor", "Tools"],
    messages: [
      { from: 0, to: 1, label: "Goal + constraints" },
      { from: 1, to: 2, label: "Linear plan [1..N]" },
      { from: 2, to: 3, label: "Execute step 1" },
      { from: 3, to: 2, label: "Step result", reply: true },
      { from: 2, to: 3, label: "Execute remaining steps" },
      { from: 3, to: 2, label: "Execution trace", reply: true },
      { from: 2, to: 0, label: "Synthesized outcome", reply: true },
    ],
  },
  "multi-path-plan": {
    participants: ["User", "Planner", "Evaluator", "Executor"],
    messages: [
      { from: 0, to: 1, label: "Goal + constraints" },
      { from: 1, to: 2, label: "Candidate paths A, B, C" },
      { from: 2, to: 1, label: "Scores + selected path", reply: true },
      { from: 1, to: 0, label: "Alternatives for review", reply: true },
      { from: 0, to: 3, label: "Confirm route" },
      { from: 3, to: 0, label: "Executed outcome", reply: true },
    ],
  },
  "self-reflection": {
    participants: ["User", "Planner", "Reflector", "Tools"],
    messages: [
      { from: 0, to: 1, label: "Goal" },
      { from: 1, to: 2, label: "Draft plan" },
      { from: 2, to: 1, label: "Critique + inconsistencies", reply: true },
      { from: 1, to: 2, label: "Revised plan" },
      { from: 2, to: 1, label: "Accept / revise", reply: true },
      { from: 1, to: 3, label: "Execute verified plan" },
      { from: 3, to: 0, label: "Result", reply: true },
    ],
  },
  "voting-cooperation": {
    participants: ["User", "Coordinator", "Voter agents", "Aggregator"],
    messages: [
      { from: 0, to: 1, label: "Decision task" },
      { from: 1, to: 2, label: "Same task to N voters" },
      { from: 2, to: 1, label: "Independent votes", reply: true },
      { from: 1, to: 3, label: "Votes + confidence" },
      { from: 3, to: 1, label: "Majority / weighted result", reply: true },
      { from: 1, to: 0, label: "Final decision", reply: true },
    ],
  },
  "role-based-cooperation": {
    participants: ["User", "Orchestrator", "Specialist roles", "Shared memory"],
    messages: [
      { from: 0, to: 1, label: "Complex task" },
      { from: 1, to: 2, label: "Assign role-scoped work" },
      { from: 2, to: 3, label: "Write artifacts + status" },
      { from: 3, to: 2, label: "Prior role output", reply: true },
      { from: 2, to: 1, label: "Specialist deliverables", reply: true },
      { from: 1, to: 0, label: "Integrated result", reply: true },
    ],
  },
  "debate-cooperation": {
    participants: ["User", "Debate coordinator", "Debater agents", "Judge"],
    messages: [
      { from: 0, to: 1, label: "Decision question" },
      { from: 1, to: 2, label: "Request initial positions" },
      { from: 2, to: 1, label: "Arguments", reply: true },
      { from: 1, to: 2, label: "Share peers' evidence" },
      { from: 2, to: 1, label: "Rebuttals for K rounds", reply: true },
      { from: 1, to: 3, label: "Debate transcript" },
      { from: 3, to: 0, label: "Verdict + rationale", reply: true },
    ],
  },
  "registry-adapter": {
    participants: ["User", "Orchestrator", "Registry", "Adapter", "Capability"],
    messages: [
      { from: 0, to: 1, label: "Task" },
      { from: 1, to: 2, label: "Discover matching capability" },
      { from: 2, to: 1, label: "Metadata + endpoint", reply: true },
      { from: 1, to: 3, label: "Uniform invocation" },
      { from: 3, to: 4, label: "Framework-specific call" },
      { from: 4, to: 3, label: "Raw result", reply: true },
      { from: 3, to: 1, label: "Normalized result", reply: true },
      { from: 1, to: 0, label: "Response", reply: true },
    ],
  },
  "parallel-fanout": {
    participants: ["User", "Initiator", "Specialist agents", "Synthesizer"],
    messages: [
      { from: 0, to: 1, label: "Complex task" },
      { from: 1, to: 2, label: "Fan out N independent tasks" },
      { from: 2, to: 1, label: "Parallel results", reply: true },
      { from: 1, to: 3, label: "Results + failures" },
      { from: 3, to: 1, label: "Merged analysis", reply: true },
      { from: 1, to: 0, label: "Synthesized response", reply: true },
    ],
  },
  "hierarchical-decomposition": {
    participants: ["User", "Root agent", "Mid-level agents", "Workers", "Tools"],
    messages: [
      { from: 0, to: 1, label: "Open-ended task" },
      { from: 1, to: 2, label: "Delegate domain goals" },
      { from: 2, to: 3, label: "Decompose into worker tasks" },
      { from: 3, to: 4, label: "Execute scoped actions" },
      { from: 4, to: 3, label: "Tool results", reply: true },
      { from: 3, to: 2, label: "Worker outputs", reply: true },
      { from: 2, to: 1, label: "Domain synthesis", reply: true },
      { from: 1, to: 0, label: "Final synthesis", reply: true },
    ],
  },
  swarm: {
    participants: ["User", "Dispatcher", "Peer agents", "Consensus check"],
    messages: [
      { from: 0, to: 1, label: "Collaborative task" },
      { from: 1, to: 2, label: "Select first peer" },
      { from: 2, to: 2, label: "Peer handoffs + critique" },
      { from: 2, to: 3, label: "Check consensus / limit" },
      { from: 3, to: 2, label: "Continue or terminate", reply: true },
      { from: 2, to: 1, label: "Emergent solution", reply: true },
      { from: 1, to: 0, label: "Final outcome", reply: true },
    ],
  },
  "human-in-the-loop": {
    participants: ["User", "Agent", "Risk classifier", "Human approver", "Tool"],
    messages: [
      { from: 0, to: 1, label: "Goal" },
      { from: 1, to: 2, label: "Classify proposed action" },
      { from: 2, to: 1, label: "Low / medium / high risk", reply: true },
      { from: 1, to: 3, label: "High-risk approval request" },
      { from: 3, to: 1, label: "Approve / reject + identity", reply: true },
      { from: 1, to: 4, label: "Execute approved action" },
      { from: 4, to: 1, label: "Action result", reply: true },
      { from: 1, to: 0, label: "Outcome + audit trail", reply: true },
    ],
  },
  "generator-critic": {
    participants: ["User", "Generator", "Critic", "Quality gate"],
    messages: [
      { from: 0, to: 1, label: "Task + criteria" },
      { from: 1, to: 2, label: "Draft artifact" },
      { from: 2, to: 1, label: "Must-fix critique", reply: true },
      { from: 1, to: 2, label: "Revised draft" },
      { from: 2, to: 3, label: "Score + evidence" },
      { from: 3, to: 1, label: "Pass or iterate", reply: true },
      { from: 1, to: 0, label: "Accepted artifact", reply: true },
    ],
  },
  "subagent-spawning": {
    participants: ["User", "Parent agent", "Sub-agents", "Shared workspace"],
    messages: [
      { from: 0, to: 1, label: "Large task" },
      { from: 1, to: 2, label: "Spawn scoped agents" },
      { from: 2, to: 3, label: "Parallel reads / edits" },
      { from: 3, to: 2, label: "Files + shared state", reply: true },
      { from: 2, to: 1, label: "Results + conflicts", reply: true },
      { from: 1, to: 0, label: "Merged outcome", reply: true },
    ],
  },
  "skill-library": {
    participants: ["User", "Agent", "Skill library", "Tools"],
    messages: [
      { from: 0, to: 1, label: "Task" },
      { from: 1, to: 2, label: "Search reusable skills" },
      { from: 2, to: 1, label: "Ranked procedures", reply: true },
      { from: 1, to: 3, label: "Execute adapted skill" },
      { from: 3, to: 1, label: "Result", reply: true },
      { from: 1, to: 2, label: "Save validated skill" },
      { from: 1, to: 0, label: "Response", reply: true },
    ],
  },
  "dual-llm-security": {
    participants: ["User", "Quarantined LLM", "Validator", "Privileged LLM", "Tool"],
    messages: [
      { from: 0, to: 1, label: "Untrusted content" },
      { from: 1, to: 2, label: "Symbolic primitives" },
      { from: 2, to: 3, label: "Validated operation" },
      { from: 3, to: 4, label: "Privileged tool call" },
      { from: 4, to: 3, label: "Tool result", reply: true },
      { from: 3, to: 2, label: "Safe response", reply: true },
      { from: 2, to: 0, label: "Outcome", reply: true },
    ],
  },
  "core-memory": {
    participants: ["User", "Agent", "Core memory", "LLM"],
    messages: [
      { from: 0, to: 1, label: "Message" },
      { from: 1, to: 2, label: "Read identity + preferences" },
      { from: 2, to: 1, label: "Always-visible facts", reply: true },
      { from: 1, to: 3, label: "Message + core memory" },
      { from: 3, to: 1, label: "Personalized response", reply: true },
      { from: 1, to: 2, label: "Update stable facts" },
      { from: 1, to: 0, label: "Response", reply: true },
    ],
  },
  "archival-memory": {
    participants: ["User", "Agent", "Archive", "LLM"],
    messages: [
      { from: 0, to: 1, label: "Question" },
      { from: 1, to: 2, label: "Search long-term memory" },
      { from: 2, to: 1, label: "Relevant records", reply: true },
      { from: 1, to: 3, label: "Question + recalled facts" },
      { from: 3, to: 1, label: "Answer", reply: true },
      { from: 1, to: 2, label: "Archive new durable fact" },
      { from: 1, to: 0, label: "Response", reply: true },
    ],
  },
  "recall-memory": {
    participants: ["User", "Agent", "Recall store", "LLM"],
    messages: [
      { from: 0, to: 1, label: "Follow-up question" },
      { from: 1, to: 2, label: "Search conversation history" },
      { from: 2, to: 1, label: "Relevant prior messages", reply: true },
      { from: 1, to: 3, label: "Current + recalled context" },
      { from: 3, to: 1, label: "Continuous response", reply: true },
      { from: 1, to: 2, label: "Append new exchange" },
      { from: 1, to: 0, label: "Response", reply: true },
    ],
  },
  "scratchpad-memory": {
    participants: ["User", "Agent", "Scratchpad", "LLM"],
    messages: [
      { from: 0, to: 1, label: "Multi-step task" },
      { from: 1, to: 2, label: "Read working notes" },
      { from: 2, to: 1, label: "Partial state", reply: true },
      { from: 1, to: 3, label: "Task + current state" },
      { from: 3, to: 1, label: "Next result", reply: true },
      { from: 1, to: 2, label: "Append / replace notes" },
      { from: 1, to: 0, label: "Progress response", reply: true },
    ],
  },
  "shared-memory": {
    participants: ["User", "Agent A", "Shared memory", "Agent B"],
    messages: [
      { from: 0, to: 1, label: "Project task" },
      { from: 1, to: 2, label: "Write goals + progress" },
      { from: 3, to: 2, label: "Read shared state" },
      { from: 2, to: 3, label: "Latest project context", reply: true },
      { from: 3, to: 2, label: "Write specialist result" },
      { from: 2, to: 1, label: "Coordinated state", reply: true },
      { from: 1, to: 0, label: "Integrated response", reply: true },
    ],
  },
};

export const patterns: Pattern[] = patternDrafts.map((pattern) => ({
  ...pattern,
  ...qualityProfiles[pattern.id],
  sequence: sequenceProfiles[pattern.id],
}));

export const categoryCounts = patterns.reduce<Record<PatternCategory, number>>(
  (counts, pattern) => {
    counts[pattern.category] += 1;
    return counts;
  },
  { "Single agent": 0, "Multi-agent": 0, Memory: 0 },
);
