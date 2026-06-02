## Parent PRD

`issues/prd.md`

## What to build

Apply the structured error model to chat streaming failures. Chat provider, retrieval, prompt, and persistence failures should produce parseable SSE error events and never leave the UI stuck on a streaming placeholder.

## Acceptance criteria

- [ ] Chat SSE error events use the structured app error shape.
- [ ] Frontend parses structured chat errors and remains compatible with older error payloads.
- [ ] Failed chat streams replace empty assistant drafts with a friendly message.
- [ ] Failed chat streams preserve the user's original question.
- [ ] No dedicated per-message retry button is added.
- [ ] Chat input becomes usable again after a stream failure ends.
- [ ] Raw technical chat failure details are logged, not rendered in the main page.
- [ ] Backend chat stream tests cover structured SSE errors.
- [ ] Frontend lint, typecheck, and build remain green.

## Blocked by

- Blocked by `issues/002-add-structured-app-error-contract.md`
- Blocked by `issues/005-frontend-operation-state-guards.md`

## User stories addressed

- User story 38
- User story 39
- User story 40
- User story 41
- User story 42
- User story 43
- User story 50
- User story 51
- User story 56
- User story 57
