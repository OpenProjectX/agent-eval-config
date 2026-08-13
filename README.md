# AgentEval configuration

Git-managed configuration for the AgentEval demo. The application owns the
runner implementation; this repository contains only declarative, immutable
agent, tool, dataset, and policy revisions.

## Demo contents

- `demo-assistant@1`: the original OpenAI example
- `demo-assistant@2`: an Anthropic-compatible deployment example
- `demo-assistant@4`: adds the governed Bash sandbox audit probe
- `demo-assistant@5`: adds arbitrary Bash execution inside governed OpenShell
- `calculator.evaluate@1`: deterministic arithmetic
- `datetime.now@1`: current date/time lookup
- `weather.lookup@1`: mocked weather lookup for repeatable evaluations
- `bash.audit@1`: fixed sandbox access probes; it does not accept arbitrary commands
- `bash.execute@1`: arbitrary multiline Bash with timeout and bounded output;
  classified destructive and intended only for governed OpenShell runs
- `smoke@3`: five evaluation cases, including fixed access checks and arbitrary Bash

## Change workflow

1. Copy the latest revision and increment its revision number.
2. Select published tool IDs and exact versions from `tools/`.
3. Run `python scripts/validate.py`.
4. Open a pull request.
5. Jenkins validates the configuration and triggers the dedicated
   `AgentEval-evaluate-agent` pipeline. The pinned runner executes in OpenShell;
   AgentEval stores score/trace correlations while semantic payloads remain in
   Langfuse.

Drafts and preview runs belong in the AgentEval database, not in Git. API keys
and other credentials must be stored in Kubernetes Secrets and referenced by a
credential profile; never commit secret values here.

## Extending tools

For the PoC, users can add a declarative HTTP or MCP tool definition by copying
one of the built-in files and changing `spec.type`, connection metadata, and
schemas. A maintainer reviews and publishes it through a pull request. Custom
Python code is intentionally not loaded from this repository.

Tool implementations remain behind the AgentEval Tool Gateway. Built-in tools
use a trusted handler name; HTTP and MCP definitions are resolved by gateway
adapters. This keeps the agent runner image unchanged.

`bash.execute` is the deliberate exception to the read-oriented demo catalog.
Its GitOps definition grants access to the trusted runner handler; it does not
provide isolation. OpenShell policy, non-root execution, and Tetragon observation
must surround governed use. The runner limits scripts to 32 KiB, time to 30
seconds, and combined output to 64 KiB, then kills the Bash process group.
