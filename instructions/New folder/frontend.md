
# Frontend Development Instructions

## Stack
- Next.js App Router.
- TypeScript strict mode.
- Tailwind CSS.
- Recharts.
- Lucide icons.

## Design direction
Build EventWise AI using a polished Modern Mario-inspired visual style.

### Colors
- Sky blue: #8EDBFA
- Red: #E8483F
- Green: #279B52
- Coin gold: #FFC928
- White: #FFFFFF
- Deep navy: #20304A
- Soft background: #F4FAFF
- Muted text: #64748B

### Visual language
- Use playful sky, cloud, grass, pipe, coin, star, and brick motifs.
- Use original CSS illustrations or SVGs.
- Use pixel-inspired fonts sparingly for headings.
- Use readable sans-serif typography for forms, budgets, and body text.
- Use rounded cards, restrained outlines, and subtle shadows.
- Keep the application professional rather than resembling a full-screen game.

## Pages
- Dashboard: events, summary metrics, tasks, and recent activity.
- Planner: event creation and plan generation.
- Event details: recommendations, budget, timeline, and chat.
- Budget: allocations, actual expenses, remaining funds, and charts.
- Chat: event-specific follow-up conversations.
- Knowledge base: uploads, indexing, search, preview, and deletion.

## API integration
- Use a centralized API client in lib/api.ts.
- Configure the backend URL through an environment variable.
- Never call Ollama directly from the browser.
- Never access ChromaDB or SQLite from the browser.
- Use explicit TypeScript request and response types.
- Handle network errors, validation errors, and backend unavailability.

## Data integrity
- Backend calculations are authoritative.
- Display estimated costs clearly.
- Show source citations returned by the backend.
- Do not invent live vendor prices or availability.
- Do not use fake dashboard metrics as actual persisted data.

## Accessibility
- Use semantic HTML and accessible labels.
- Support keyboard navigation and visible focus states.
- Maintain readable contrast.
- Do not rely on color alone for task status.
- Respect reduced-motion preferences.
- Make all major screens usable on mobile, tablet, and desktop.

## Code quality
- Prefer small reusable components.
- Avoid unnecessary client components.
- Avoid `any`.
- Validate forms using appropriate schemas.
- Reuse existing design conventions.
- Provide loading, empty, success, and error states.

## Verification
- Run linting and TypeScript checks.
- Test form validation and API error states.
- Verify navigation and responsive layouts.
- Ensure buttons perform their advertised actions.
