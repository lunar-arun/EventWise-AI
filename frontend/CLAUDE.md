# Frontend Development Instructions

## Stack
- Next.js App Router
- TypeScript strict mode
- Tailwind CSS
- Recharts
- Lucide icons
- React Hook Form & Zod

## Design Direction
Build EventWise AI using a polished Modern Mario-inspired visual style.

### Colors
- Sky blue: `#8EDBFA`
- Red: `#E8483F`
- Green: `#279B52`
- Coin gold: `#FFC928`
- White: `#FFFFFF`
- Deep navy: `#20304A`
- Soft background: `#F4FAFF`
- Muted text: `#64748B`

### Visual Language
- Use playful sky, cloud, grass, pipe, coin, star, question-block, and brick motifs.
- Use original CSS illustrations or SVGs.
- Use pixel-inspired fonts sparingly for selected headings and small game-level badges.
- Use readable sans-serif typography for forms, budgets, tables, and body text.
- Use rounded cards, restrained outlines, and subtle shadows.
- Keep the application professional rather than resembling a full-screen game.

## Pages
- **Dashboard (`/`)**: events, summary metrics, level-styled upcoming events, task quests, quick actions, and recent activity.
- **Planner (`/planner`)**: event creation and AI + RAG plan generation.
- **Event Details (`/events/[id]`)**: event summary, recommendations, budget breakdown, timeline, task checklist, source citations, preference editing, and contextual chat.
- **Event Timeline (`/events/[id]/timeline`)**: chronological quest-style timeline and interactive task status management.
- **Budget (`/budget`)**: allocations, actual expenses, remaining funds, overrun warnings, emergency reserve, cost-reduction tips, and Recharts visualizations.
- **Chat (`/chat`)**: event-specific follow-up conversations with safe proposal preview and approval.
- **Knowledge Base (`/knowledge-base`)**: file uploads, structured entry creation/editing, indexing status, semantic search, passage previews, re-indexing, and deletion.

## API Integration
- Use a centralized API client in `lib/api.ts`.
- Configure the backend URL through `NEXT_PUBLIC_API_BASE_URL` (defaulting to `http://localhost:8000`).
- Never call Ollama directly from the browser.
- Never access ChromaDB or SQLite from the browser.
- Use explicit TypeScript request and response types.
- Handle network errors, validation errors, and backend unavailability gracefully.

## Data Integrity
- Backend calculations are authoritative.
- Display estimated costs clearly as illustrative estimates.
- Show real source citations returned by the backend.
- Do not invent live vendor prices or availability.
- Do not use fake dashboard metrics as actual persisted data.

## Accessibility
- Use semantic HTML and accessible labels.
- Support keyboard navigation and visible focus states.
- Maintain readable contrast with `#20304A` deep navy text.
- Do not rely on color alone for task status.
- Respect reduced-motion preferences (`prefers-reduced-motion`).
- Make all major screens usable on mobile, tablet, and desktop.

## Code Quality
- Prefer small reusable components.
- Avoid `any`.
- Validate forms using Zod schemas and HTML5 constraints.
- Provide loading, empty, success, and error states.

## Verification
- Run linting and TypeScript checks (`npm run typecheck`, `npm run build`).
- Test form validation and API error states.
- Verify navigation and responsive layouts.
- Ensure buttons perform their advertised actions.
