# Hermes adapter

Run `mcp_server.py` as a local stdio MCP server. It exposes:

```text
agent_body_emit(event, summary?, mode?, consent?)
```

The tool posts only to `http://127.0.0.1:5051/event`; start the mapper on the same host first:

```bash
agent-body serve --hal http://127.0.0.1:5001
```

Recommended lifecycle mapping:

- session/tool work starts → `started` or `thinking`
- user decision required → `waiting_for_user`
- permission gate → `permission_required`
- repeated tool error → `blocked`
- test result → `tests_passed` / `tests_failed`
- session task complete → `completed`
- focus/night transition → `quiet`

Register it in Hermes config (restart Hermes after adding):

```yaml
mcp_servers:
  agent-body:
    command: python3
    args: ["/absolute/path/to/agent-body-protocol/adapters/hermes/mcp_server.py"]
```

The tool appears as `mcp_agent_body_agent_body_emit`. The adapter is transport-only; it does not inspect session transcripts or secrets.
