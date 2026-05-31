# AgentDevInsight Python SDK

Python SDK for the [AgentDevInsight](https://github.com/agentdevinsight) AI Agent Observability Platform.

Sends traces, spans, generations and scores to the platform's LangFuse-compatible public API.

## Installation

```bash
# Development install
pip install -e .

# From PyPI (when published)
pip install agentdevinsight

# With LangChain callback support
pip install agentdevinsight[langchain]
```

## Configuration

Set environment variables (or pass them directly to the client):

| Variable | Default | Description |
|---|---|---|
| `AGENTDEVINSIGHT_BASE_URL` | `http://localhost:8000` | Platform base URL |
| `AGENTDEVINSIGHT_API_KEY` | *(none)* | Optional bearer token |

## Quick start

### 1. `@trace` decorator

The easiest way to instrument a function:

```python
from agentdevinsight import trace

@trace(name="my_agent")
def my_agent(query: str) -> str:
    # your agent logic here
    return call_llm(query)
```

Every call automatically creates a trace with input, output, latency, and
error information.

### 2. Low-level client

For full control over traces, spans, generations and scores:

```python
from agentdevinsight import AgentDevInsightClient

client = AgentDevInsightClient()

# Create a trace
trace = client.create_trace("my-run")
trace_id = trace["data"]["id"]

# Create a span
span = client.create_span(trace_id, "llm-call", type="llm")
span_id = span["data"]["id"]

# Record a generation
client.create_generation(span_id, model="gpt-4", prompt="Hello", completion="Hi!")

# Attach a score
client.create_score(trace_id, "quality", 0.95)
```

### 3. Context manager style

```python
from agentdevinsight import AgentDevInsightClient

client = AgentDevInsightClient()

with client.trace("my-agent") as t:
    with t.span("retrieval") as s:
        docs = retrieve("query")
    with t.span("llm", type="llm") as s:
        s.generation(model="gpt-4", prompt="...", completion="answer")
    t.score("relevance", 0.9)
```

### 4. LangChain integration

```python
from agentdevinsight.callbacks import AgentDevInsightCallbackHandler
from langchain_openai import ChatOpenAI

handler = AgentDevInsightCallbackHandler()

llm = ChatOpenAI(callbacks=[handler])
response = llm.invoke("What is the capital of France?")
```

The handler maps LangChain events to traces, spans and generations:

| LangChain event | AgentDevInsight entity |
|---|---|
| `on_chain_start` | Trace created |
| `on_chain_end` | Trace completed |
| `on_llm_start` | Span (type `llm`) |
| `on_llm_end` | Generation with prompt/completion |
| `on_tool_start` | Span (type `tool`) |
| `on_tool_end` | Span output recorded |
