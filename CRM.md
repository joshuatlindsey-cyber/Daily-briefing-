# Atlas CRM

An S-tier, single-file CRM for creators — sponsors, collaborators, podcast guests, clients, leads and superfans, all in one place. No build step, no server, no dependencies. Open `crm.html` and it works.

## Open it

- **Locally:** double-click `crm.html` (or open it in any browser).
- **Hosted:** enable GitHub Pages for this repo and visit `…/crm.html`.

Your data is saved automatically to the browser's `localStorage`. The app ships with demo data on first run so you can see it in action immediately.

## Features

- **Dashboard** — KPIs (contacts, active deals, pipeline value, open/overdue tasks), a pipeline funnel, recent activity and upcoming follow-ups.
- **Contacts** — card or table view, filter by type, sortable columns, full-text search. Each contact has a detail drawer with details, notes, tasks and an activity timeline.
- **Pipeline** — a drag-and-drop Kanban board across stages (Lead → Contacted → Negotiating → Won → Lost). Moving a card logs the stage change and updates totals.
- **Tasks** — follow-ups tied to contacts, with due dates and overdue/today highlighting. Check them off as you go.
- **Activity log** — log notes, calls, emails, DMs and meetings per contact.
- **Export / Import** — download everything as JSON (full backup) or contacts as CSV; re-import JSON on any device. Reset to demo data anytime.
- **Theming** — dark and light, remembered between sessions.

## Keyboard shortcuts

| Key | Action |
| --- | --- |
| `/` | Focus search |
| `n` | New contact |
| `1` `2` `3` `4` | Dashboard · Contacts · Pipeline · Tasks |
| `Esc` | Close any panel |

## Data model

Each contact: `name`, `company`, `type`, `stage`, `value`, `email`, `phone`, `handle`, `tags[]`, `notes`, plus `activity[]` (timeline) and `tasks[]` (follow-ups). All state lives client-side in `localStorage` under the key `atlas_crm_v1`.

## Roadmap ideas

This is a polished MVP. Natural next steps: sync to a backend for multi-device, pull subscribers in from Kit, sync follow-ups to Google Calendar, and bulk actions / saved segments.
