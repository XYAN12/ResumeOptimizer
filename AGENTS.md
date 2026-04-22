# Resume Improver Repository Instructions

## Project goal
Build a production-like resume optimization agent application.
The system must help users compare a resume against a target job description, produce grounded analysis, and generate an improved resume version that stays faithful to the original facts.

## Non-negotiable rules
1. Never invent facts that are not present in the original resume.
2. The optimized resume must only reorganize, clarify, prioritize, and rephrase existing facts.
3. All API keys and secrets must come from environment variables.
4. Do not hardcode credentials, tokens, or local machine paths.
5. Keep the project Docker-runnable from the repository root.
6. Keep README.md accurate and sufficient for a stranger to run the app.

## Product requirements
The app must support:
- uploading resume files (pdf, docx, md, txt)
- pasting resume text directly
- inputting a target JD
- producing:
  - match highlights
  - major gaps
  - concrete suggestions
- requiring user confirmation before final resume generation
- exporting optimized resume as md, docx, and pdf

## Architecture requirements
Use clear separation of responsibilities.
Preferred backend modules:
- parser
- normalization
- fact extraction
- jd analysis
- gap analysis
- rewrite service
- export service

The rewrite stage must consume structured facts rather than raw resume text whenever possible.

## Fact-grounding policy
Every generated optimization should be traceable back to source resume content.
Prefer structured intermediate representations such as:
- personal info
- education
- experience
- projects
- skills
- awards
- languages

If confidence is low, preserve the original wording instead of making stronger claims.

## Preferred stack
- Backend: Python + FastAPI
- Frontend: React or Next.js
- Containerization: Docker
- Document export: markdown + docx + pdf
- LLM provider: configurable via environment variables

## Development workflow
When implementing a large feature:
1. propose a short implementation plan
2. inspect existing code before editing
3. make focused changes
4. run the smallest meaningful validation
5. summarize what changed

## Code quality
- Use type hints where reasonable
- Keep functions small and testable
- Add docstrings for non-trivial logic
- Prefer explicit data models over loose dict chains
- Handle invalid input gracefully
- Log useful debugging information without exposing PII or secrets

## Testing
At minimum, validate:
- text resume input flow
- file upload flow
- JD analysis flow
- grounded rewrite flow
- export flow
- API failure path
- invalid file type handling

## README requirements
README.md must include:
- project overview
- architecture summary
- setup instructions
- environment variables
- docker build and run commands
- example usage
- known limitations

## Review checklist
Before finishing, verify:
- the app runs from Docker
- no secrets are committed
- .env.example exists
- export works
- generated resume is grounded in original facts
- README steps are reproducible