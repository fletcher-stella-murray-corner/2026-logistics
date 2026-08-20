# Open Questions

Unresolved project-level questions (naming, hosting, etc.) that don't block current work but shouldn't be forgotten. Remove an entry once it's decided — fold the decision into the doc it actually belongs in (`way-of-working.md`, `brand-guidelines.md`, etc.), don't leave a stale answer here.

## Person-chip initials can collide

The Structures stage and the Timeline's Arrivals/Departures rows render a person as a tap-to-reveal initials chip, not their name directly (see `brand-guidelines.md` → *Illustration / Imagery Style* and `requirements/public.md` → *The Structures stage* → *Nested box display*): a single-word display name takes its own first two letters ("Stella" → "ST"), a multi-word one (already carrying a disambiguating last initial, e.g. "Helen S") takes one letter per word ("HS") — see `person_initials()` in `timeline/scripts/build.py`. This was deliberately chosen over the plain "first letter only" scheme (which collided 5-way on "S" alone: Stella/Steven/Shawn/Shannon/Sandra), but real collisions remain for today's actual roster — checked directly against `shared/data/people.json`:

- ST: Stella, Steven
- MA: Margaret, Matt
- JE: Jesse, Jeremy
- WE: Weston, Wes
- KA: Kaylyn, Kate
- SH: Shawn, Shannon

Each pair renders an identical chip until tapped. Not a build-time error today (nothing validates against it), and not yet designed around further — a real fix (a trailing tie-breaker character, falling back to more of the name only for the colliding pair, etc.) is a real design decision worth making deliberately, not guessed at here. Re-run the check in `person_initials()`'s own docstring after any roster change to see whether the list above is still accurate.

(Roster/data-entry progress — how many people are filled in, what's still missing — is tracked by the data files themselves and git history, not here; that's status, not an unresolved question.)
