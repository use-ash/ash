# use-ash/memory

Framework for file-based agent memory.

This repository does not provide code. It provides the document structure, schemas, examples, and behavior rules an AI agent can use to implement durable memory in its own workspace.

Use this framework when an agent needs to:

- remember facts across sessions
- store corrections so mistakes do not repeat
- keep project state outside a chat transcript
- retrieve relevant notes without loading everything

Start here:

1. Read [AGENT_INSTRUCTIONS.md](AGENT_INSTRUCTIONS.md).
2. Read [MEMORY_FRAMEWORK.md](MEMORY_FRAMEWORK.md).
3. Read [SCHEMA.md](SCHEMA.md).
4. Read [FEEDBACK_GUIDE.md](FEEDBACK_GUIDE.md).
5. Copy and adapt [INDEX_TEMPLATE.md](INDEX_TEMPLATE.md).

Reference background:

- ASH wiki: <https://use-ash.github.io/ash/>
- Memory and continuity overview: <https://use-ash.github.io/ash/memory-and-continuity/>

Repository contents:

- `MEMORY_FRAMEWORK.md`: overall memory system design
- `SCHEMA.md`: frontmatter schema and memory types
- `FEEDBACK_GUIDE.md`: behavior-changing feedback loop
- `INDEX_TEMPLATE.md`: starter memory index
- `PITFALLS.md`: common failure modes and prevention rules
- `examples/`: example memory notes
