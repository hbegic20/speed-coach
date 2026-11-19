# SpeedCoach

Web performance auditor. A user pastes a URL, the API runs a Google PageSpeed (Lighthouse) audit for mobile and desktop, detects the site's platform, and an LLM turns the results into a ranked list of plain-language fixes for that platform, in Bosnian or English.

## Stack

- `web/`: Next.js (App Router), React, TypeScript (strict), Tailwind CSS, pnpm
- `api/`: Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2 (async) + Alembic, httpx, uv
- Data: PostgreSQL, Redis (job queue and cache)
- AI: Google Gemini API with structured output, validated by Pydantic
- Infra: Docker Compose for local dev, GitHub Actions CI, Vercel (web), Railway/Fly.io (api)

## Structure

```
web/
  app/            routes, layouts, server components
  components/     shared UI
  lib/            api client, utils, types
api/
  app/
    routers/      HTTP endpoints only
    services/     business logic (pagespeed, detection, llm)
    models/       SQLAlchemy models
    schemas/      Pydantic request/response models
    core/         config, db, dependencies
  tests/
docker-compose.yml
```

## Commands

```
docker compose up -d                 # postgres + redis
cd web && pnpm dev                   # web on :3000
cd api && uv run fastapi dev app/main.py   # api on :8000

cd web && pnpm lint && pnpm typecheck && pnpm test
cd api && uv run ruff check . && uv run ruff format --check . && uv run mypy . && uv run pytest
```

Run the relevant checks before reporting a task as done. Fix failures, do not silence them.

## Hard rules

- **Never commit, push, create branches, or open PRs.** Do not run `git add`, `git commit`, `git push`, `git rebase`, `git reset`, or `gh pr`. The developer reviews and commits everything. Leave changes in the working tree.
- **No comments in code.** No inline comments, block comments, JSDoc, docstrings, or TODOs. Code must explain itself through naming, small functions, and types. If something needs explaining, say it in your reply, not in the file.
- Never hardcode secrets. Read them from environment variables and keep `.env.example` up to date with names only.
- Do not add a dependency without a clear need. Prefer the platform and what is already installed. When you add one, state why in your reply.

## Code quality

Write code the way a senior engineer would ship it to production:

- Small, single-purpose functions and modules. Early returns over nesting. No dead code, no unused exports, no speculative abstractions.
- Precise naming. No abbreviations except well-known ones (`url`, `id`, `db`).
- Make invalid states unrepresentable with types. No `any`, no non-null assertions, no `# type: ignore` without a real reason.
- Handle errors at boundaries (HTTP handlers, external API calls) with typed, user-safe responses. Never swallow exceptions.
- Validate all external input: request bodies with Pydantic/Zod, URLs before fetching, LLM output against a schema.
- Keep changes focused on the task. Do not reformat or refactor unrelated code.

## Frontend: bundle size and performance

This product audits web performance, so its own pages must score 95+ on Lighthouse.

- Server Components by default. Add `"use client"` only to the smallest leaf that needs state, effects, or browser APIs.
- Fetch data on the server. No client-side data fetching libraries unless a screen truly needs live updates.
- No UI kits or icon packs. Inline SVG for icons, Tailwind for styling.
- No heavy libraries for small jobs (no lodash, moment, axios, chart libraries for simple charts). Use native APIs and small hand-written SVG charts.
- `next/font` for Inter and Space Grotesk, `next/image` for every image, `next/dynamic` for anything heavy below the fold.
- Prefer CSS over JavaScript for interactions and animations.
- Check `pnpm build` output when adding client code and keep first-load JS minimal.

## Backend

- Async all the way: async SQLAlchemy sessions, `httpx.AsyncClient`, no blocking calls in request handlers.
- Routers stay thin: parse input, call a service, return a schema. Logic lives in `services/`.
- Long-running audits run as background jobs, not inside the request.
- Cache PageSpeed results per URL and device for a short window to protect the API quota.
- Settings via `pydantic-settings`. One config object, injected through dependencies.
- Database changes only through Alembic migrations.

## Testing

- Test behavior, not implementation. Every service gets unit tests. Every endpoint gets at least a happy path and a validation-failure test.
- Mock external services (PageSpeed, Gemini) at the HTTP boundary. Tests never hit the network.

## Design

- Follow the SpeedCoach design canvas: Home, Report, Dashboard/History, Mobile Report.
- Colors: background `#F6F7F9`, text `#0F172A`, accent `#1D4ED8`, good `#047857`, needs work `#B45309`, poor `#B91C1C`. Status colors are always paired with a text label.
- Fonts: Space Grotesk for headings, Inter for body.
- Accessible by default: semantic HTML, real buttons and links, labelled inputs, visible focus, 4.5:1 text contrast, 44px touch targets.
- All user-facing text supports Bosnian (`bs`) and English (`en`).

## Working style

- For anything larger than a small fix, outline the plan briefly before writing code.
- When requirements are unclear, ask instead of guessing.
- When done, summarize what changed and which checks you ran.