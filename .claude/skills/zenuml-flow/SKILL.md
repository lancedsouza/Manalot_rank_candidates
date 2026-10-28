---
name: zenuml-flow
description: Write, fix and lint ZenUML sequence diagrams (```mermaid blocks starting with `zenuml`), including the Hybrid Chatbot flow files in docs/flows/<admin|pub>/<name>-flow.md. Use whenever a flow diagram is created, changed or renders wrongly (stray Loop/Opt boxes, missing labels, broken arrows), when a slice changes a flow, or when the user mentions ZenUML, sequence diagrams or FLOW-xx diagrams.
---

# ZenUML flow diagrams

## File shape (project convention)

- One diagram per file: `docs/flows/pub/` for flows a site visitor starts through the widget, `admin/` for everything else (dashboard, operator CLI, CI). Short kebab-case name ending `-flow.md`.
- The file is a single ```` ```mermaid ```` block. First line `zenuml`, then `title <FLOW-ID> <name>`. The FLOW-ID matches the `## <FLOW-ID>` section in `prd.md`.
- Cover the error and empty paths as well as the happy path.
- Every call that crosses HTTP gets a `//` comment on the line above it giving the method and URL in backticks, so readers can find the endpoint without opening the code. Use the route as the code registers it (`POST /v1/chat`, `GET /admin/api/me`) for our own endpoints. For external ones, use the default full URL plus the env var that overrides it, e.g. `` // `POST https://openrouter.ai/api/v1/embeddings` (OPENROUTER_BASE_URL) ``. Take URLs from the code (`internal/httpapi`, `internal/admin`, `internal/config`), never from memory. Keep the call itself short (`OpenRouter.stream(prompt)`) and put any extra detail in that same comment.
- Admin front-end URLs count too. Comment the page the actor starts from, such as the admin UI at `ADMIN_BASE_URL/admin/` or a sign-in link `ADMIN_BASE_URL/admin/#token=…`. Take them from `web/admin/app.js` and `internal/config`.
- The widget is the exception: leave out its embed tag, its host and the scripts it loads (they make the diagram unreadable). Widget calls to the API still get the plain route, e.g. `` `POST /v1/chat` ``.

## Syntax that renders reliably

```
zenuml
title FLOW-03 Admin sign-in
@Actor Admin
@Boundary UI as "admin UI"
@Control API as "admin.Server"
@Database DB as "Postgres (RLS)"

// comment on the line above a statement becomes its label
Admin->UI.submitEmail(email) {          // sync call with nested body
  status = API.login(email) {
    if("invalid email") {
      @return API->UI: 400 invalid_email   // early return to a named caller
    }
    API->API: queue email (async)        // async message: free text after ':'
    return "202 sent"
  }
}
```

Participants: give every participant one of these annotations, never a bare name:

| Annotation | Use for |
|---|---|
| `@Actor` | a person: visitor, admin, operator |
| `@Boundary` | what a person or outside system touches: widget, admin UI, HTTP handler, CLI |
| `@Control` | logic that coordinates: services, workers, jobs |
| `@Entity` | a domain object or external service with no better icon: mailer, Turnstile, OpenRouter |
| `@Database` | Postgres or any other data store |
| `@EC2`, `@ECS`, `@RDS`, `@S3`, `@IAM`, `@Lambda` | the matching AWS resource, when the flow shows deployed infrastructure |

Use `Name as "label"` for labels containing spaces or punctuation. Fragments: `if(...) {} else if(...) {} else {}`, `opt {}`, `loop(...) {}` / `while(...) {}`, `par {}`, `try {} catch {} finally {}`.

## Pitfalls (each one has broken a real diagram here)

1. **Quote every `return` value and every `if`/`loop`/`while` condition unless it is a single identifier or a simple comparison like `score >= threshold`.** ZenUML parses `return` as an expression. Commas, parentheses, `+` or `*` in an unquoted return get misparsed into stacks of empty `Loop` boxes, so `return email, tenant, thresholds (read-only)` renders as Loop, Loop, Loop, Loop. Write `return "email, tenant, thresholds (read-only)"` instead. The same happens with conditions: `if(empty, too long, quota)` renders as Loop boxes, while `if("empty, too long, quota")` renders as one labelled Alt box. The text after `:` in `A->B: text` and `@return A->B: text` is free text and needs no quotes.
2. **Prefer `if(condition)` over a comment above `opt {}`.** `if` puts the condition inside the box. A comment above `opt` floats over the previous box, which reads as if it belongs to the wrong fragment.
3. Method arguments are identifiers: `login(email)`, not `login(the email)`. Put prose in a comment or a `->` message.
4. Keep markdown backticks only in `//` comments, never in messages or names.

## After editing

Run the lint script on every file you touched and fix whatever it reports:

```
python3 .claude/skills/zenuml-flow/scripts/lint_zenuml.py docs/flows/*/*.md
```

It catches the known pitfalls; it is not a full parser. If you can, also check the render in a ZenUML/mermaid preview.
