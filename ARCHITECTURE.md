# 🏗️ CodeRecon Architecture
CodeRecon is built on a Modular Static Analysis (MSA) pattern. It treats code as structured data rather than text, utilizing Abstract Syntax Trees (AST) to build context before involving LLM reasoning.

## 1. System Overview
```
graph TD
    A[Local Repository] --> B[Static Analyzer]
    B --> C{Functional Bucketing}
    C --> D[Entry Points]
    C --> E[Core Logic]
    C --> F[Data/Utils]
    D & E & F --> G[Context Aggregator]
    G --> H[MCP Server Layer]
    H --> I[Local LLM / Ollama]
    I --> J[Recon Report / CLI Output]
```
## 2. Core Components
### 🔍 Static Analyzer (/analyzer)
The engine uses Python's native ast module to walk the file tree. It ignores boilerplate and focuses on:

Import Graphs: Mapping internal and external dependencies to identify tight coupling.

Signature Extraction: Identifying high-risk functions and central dispatchers.

Complexity Scoring: Flagging modules with high logical density for deeper auditing.

### 🧠 LLM Orchestrator (/llm)
Instead of sending raw code to the LLM, CodeRecon sends a condensed structural map.

Local-First: Defaults to llama3 via Ollama.

Context Efficiency: Uses system-level instructions to force the LLM into an "Architectural Auditor" persona, minimizing token usage.

Privacy Guard: Filters sensitive strings (env vars, hardcoded keys) before inference.

### 🔌 MCP Integration (/mcp)
CodeRecon implements the Model Context Protocol. This allows the tool to expose its analysis as:

Tools: explain, topology, and report can be called by any MCP-compliant agent (e.g., Claude Desktop).

Resources: The processed AST data is available as a standardized resource for AI consumption.

## 3. Functional Bucketing
The tool automatically classifies files based on dependency counts and logical roles:

### Bucket	Description	Criteria
Entry Points	System dispatchers and main hooks.	High fan-out, low fan-in.
Core	High-logic modules with central dependencies.	High complexity, central import node.
Data Layer	Schemas, models, and database logic.	High density of class definitions/types.
External	API clients and LLM wrappers.	Heavy use of external network libraries.
Utilities	Helper modules and reporting logic.	Low dependency count, high internal reuse.
## 4. Privacy & Philosophy
Zero-Cloud: No source code is transmitted to external servers. All analysis is performed in-memory.

Ephemeral Storage: For remote audits, repositories are cloned into a temporary directory and purged immediately upon process exit.

###No-State: The tool is stateless; it does not store your code or analysis results in a database.
