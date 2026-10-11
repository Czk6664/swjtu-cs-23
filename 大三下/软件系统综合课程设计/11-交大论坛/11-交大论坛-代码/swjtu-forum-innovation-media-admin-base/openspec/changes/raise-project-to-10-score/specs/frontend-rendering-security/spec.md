## ADDED Requirements

### Requirement: Backend-provided text is rendered safely
The frontend SHALL treat all backend-provided strings as untrusted and render them through `textContent`, safe DOM construction, or a single audited escaping helper before insertion into the DOM.

#### Scenario: Malicious post title is returned
- **WHEN** a post title contains `<script>`, event-handler attributes, or HTML tags
- **THEN** the page displays the content as inert text and does not execute script

#### Scenario: Malicious username is returned
- **WHEN** a username contains HTML or JavaScript-like content
- **THEN** every page that displays the username renders it as text only

### Requirement: Attribute values are constrained or escaped
The frontend MUST avoid placing untrusted backend strings directly into HTML attributes unless they are escaped and appropriate for that attribute context.

#### Scenario: Backend returns hostile URL-like text
- **WHEN** backend data contains quotes, angle brackets, or `javascript:` text
- **THEN** rendered attributes do not become executable links, handlers, or malformed markup

### Requirement: Unsafe rendering sites are auditable
The frontend SHALL minimize and document remaining `innerHTML` usage, and every remaining dynamic interpolation MUST be traceable to a safe rendering helper or trusted constant.

#### Scenario: Security audit searches for innerHTML
- **WHEN** an auditor searches for `innerHTML` assignments
- **THEN** each remaining assignment has a clear reason and uses only trusted HTML or escaped dynamic values

### Requirement: XSS regression tests cover major content categories
The frontend SHALL include tests or scripted checks that render malicious strings through posts, comments, users, reports, rewards, and recommendation previews.

#### Scenario: XSS regression test runs
- **WHEN** the frontend security test suite runs with malicious fixture data
- **THEN** no script executes and the malicious payload is visible only as escaped or inert text
