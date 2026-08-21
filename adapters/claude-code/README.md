# Claude Code adapter

`hook.py` consumes a Claude Code hook JSON payload on stdin and posts a protocol event to the loopback mapper.

```bash
python3 adapters/claude-code/hook.py --hook SessionStart < payload.json
python3 adapters/claude-code/hook.py --hook Stop --mode focus < payload.json
```

For a dry run, add `--print-only`. Configure the same script for `SessionStart`, `Notification`, `PermissionRequest`, `PostToolUseFailure`, and `Stop` in Claude Code hooks. Test-result classification is deliberately best-effort; for deterministic CI state, call `agent-body post --event tests_passed` or `tests_failed` from the test command.

This adapter does not alter Autonomous Buddy's `:5002` authentication or approval flow.
