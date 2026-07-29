# Open Questions

Unresolved project-level questions (naming, hosting, etc.) that don't block current work but shouldn't be forgotten. Remove an entry once it's decided — fold the decision into the doc it actually belongs in (`way-of-working.md`, `brand-guidelines.md`, etc.), don't leave a stale answer here.

- **Real family roster** — `shared/data/people.json`, `timeline/data/travel.json`, and `timeline/data/meals.json` are all empty now (sample data removed). Site renders correctly empty in the meantime. Fill in once the real 27-person roster/travel plans/meal plan are provided.
- **DEBUG outlines still live** — the dashed red/blue outlines around each day quarter canvas and its padding spacer (`timeline/shared.css`, marked `DEBUG`) are intentionally still in place on the real site, kept around in case more layout debugging is needed before real data goes in. Remove the two `DEBUG`-marked rules in `timeline/shared.css` once they're no longer needed — real family members currently see them.
