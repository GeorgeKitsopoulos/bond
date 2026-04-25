# Bond Capability Expansion Plan (Current-State Critical Analysis)

> Historical note: this document is preserved for design rationale or implementation history. It is not the current source of truth. Use the current docs and code for present behavior, paths, and project status.

## Document status

This document is a planning and architecture artifact for an LLM to use when deciding how to evolve Bond’s capabilities from the current repository state.

It is intentionally:

- grounded in the current snapshot structure
- constrained by the separate router/brain redesign plan
- focused on capabilities, system detection, tool use, policy, and cross-platform branching
- explicit about what is known, what is missing, and what should happen next
- free of shell commands and execution steps

This document does **not** redesign the router/brain. That area is already covered by the separate router/agent redesign document and should be treated as an external constraint, not re-opened here.

---

## Inputs used

### Repository snapshot reviewed

The current snapshot includes, at minimum, the following capability-relevant areas:

- `src/bond/ai_scan_system.py`
- `src/bond/ai_exec.py`
- `src/bond/ai_action_catalog.py`
- `src/bond/ai_action_policy.py`
- `src/bond/ai_run.py`
- `docs/ARCHITECTURE.md`
- `docs/STATE.md`
- `docs/CURRENT_PATHS.md`
- `docs/BEHAVIOR_CONTRACT.md`

### External planning constraint

The router/agent redesign document is treated as authoritative for brain-layer direction:

- small front coordination
- stronger policy layer
- specialists with narrow contracts
- 20B as rare escalation only

This document therefore avoids re-planning the “brain” and instead designs the capability layer that the brain must sit on top of.

---

## Executive conclusion

Bond already has the beginnings of the right shape, but not yet the right capability architecture.

The current project appears to be ahead in these areas:

- repository discipline
- memory separation
- path normalization
- basic system inspection
- basic action policy
- documentation structure
- self-test culture

It is still behind in the areas that actually make an assistant broadly useful:

- capability taxonomy
- structured system-fact collection
- tool abstraction
- cross-platform branching
- app/session awareness
- default-app resolution
- rootless-first host integration
- honest capability negotiation
- action/result schemas
- confirmation and execution UX
- portable adapter design

The main mistake to avoid is this:

> Do not turn Bond into a pile of ad-hoc commands.

That path produces fragile demos, not a useful assistant.

The correct direction is:

> Build a capability stack with deterministic detection, typed adapters, policy-gated actions, portable contracts, and rootless-first host integration.

---

## Critical reading of the current snapshot

## What the snapshot already gets right

### 1. It is already moving toward deterministic grounding

The current repository direction explicitly favors deterministic local grounding over fake assistant improvisation. That is correct and should be reinforced, not weakened.

### 2. There is already a distinct policy instinct

`ai_action_policy.py` shows that the project already understands a key truth: unrestricted path or action handling is unacceptable. The current allow/block logic is still narrow, but the instinct is correct.

### 3. The project already has a target registry mindset

`ai_action_catalog.py` is not just a parser convenience. It shows the beginning of an abstraction layer between natural language targets and real filesystem/system objects. That is an important foundation.

### 4. The system scan exists

`ai_scan_system.py` already tries to collect meaningful facts:

- session type
- desktop/session environment
- browser/mail/file manager/editor candidates
- desktop entries
- Cinnamon-specific settings
- Flatpak and Snap visibility
- XDG handlers

That is better than many hobby assistants that blindly assume the environment.

### 5. The project already rejects “assistant theater”

The docs explicitly say Bond is not a fake do-everything assistant. That is good. Capability honesty should remain part of the product identity.

---

## What is structurally weak right now

### 1. System scan is still Linux-desktop-biased and partly heuristic

The current scan is useful, but it mixes:

- direct shell calls
- desktop heuristics
- installed binary detection
- desktop entry parsing
- environment variable checks

That is acceptable for an early Mint-first phase, but it is not yet a durable capability substrate.

The main weakness is that it collects facts without clearly separating:

- **authoritative facts**
- **derived facts**
- **guesses**
- **desktop-specific interpretations**
- **capabilities exposed to the assistant**

That distinction matters.

Example:
“nemo exists” is not the same as “Nemo is default file manager.”
“xdg handler says browser desktop ID” is stronger than “binary exists.”
“DISPLAY exists” is not the same as “GUI interaction is safe right now.”

### 2. Actions are too close to command habits

The current direction suggests Bond can already perform bounded actions, but the architecture still smells too command-centric.

That is a problem because assistants should not think in terms of:

- arbitrary shell strings
- brittle program-specific verbs
- untyped outputs

They should think in terms of **capabilities** such as:

- open a URI
- show a file in file manager
- compose an email
- inspect a system fact
- enumerate installed apps
- read clipboard
- start a timer
- create a note
- summarize selected text
- search current screen context

The implementation may map those to commands or APIs, but the assistant layer should never treat raw commands as the native abstraction.

### 3. There is no complete capability registry

Right now Bond appears to have pieces of functionality, but not a formal machine-readable registry that answers questions like:

- What can this host do?
- Which actions are read-only vs write vs privileged?
- Which backends are available?
- Which backends are preferred on this OS and desktop?
- Which actions require confirmation?
- Which actions are interactive?
- Which actions are rootless?
- Which actions are portal-backed?
- Which actions are sandbox-safe?
- Which actions are degraded but still possible?

Without that registry, the model will over-guess.

### 4. There is no clean adapter boundary

The current codebase appears to be in the phase where “logic and platform calls still touch too closely.”
That becomes a scaling problem the moment Bond branches to:

- another Linux desktop
- another Linux distro
- macOS
- Windows
- Android

The right unit of scale is not “more if-statements.”
It is “more adapters implementing the same capability contract.”

### 5. Rootless-first is not yet elevated to a first-class design rule

The project mentions safe and disciplined local operation, but rootless-first should become explicit architectural policy:

- prefer user-level APIs
- prefer portals when available
- prefer user services over system services
- prefer app handoff over direct invasive manipulation
- prefer read-only inspection over mutation
- prefer confirmation for side effects
- treat privilege escalation as an explicit alternate lane

At the moment this seems more like a preference than a governing principle. It should become a hard design constraint.

### 6. The system currently risks over-scanning and under-structuring

A common trap is gathering lots of system facts that are not turned into stable assistant decisions.
That produces noisy profiles without better behavior.

Bond should not ask:
“What can I scrape from the system?”

It should ask:
“What facts do I need in order to safely expose useful capabilities?”

---

## Research finding: what popular embedded assistants actually optimize for

## Important honesty note about the “top 100 prompts” request

There is no trustworthy public source that provides a real cross-platform ranked list of the exact top 100 most-used prompts across Siri, Gemini, Copilot, Mycroft, and similar assistants.

Those companies publish:

- examples
- capability docs
- feature pages
- user guides
- connected-app help pages
- voice UX guidance

They do **not** generally publish a verified global ranking of the top 100 requests.

So the correct move is not to fake a ranking.

The correct move is to derive a **high-confidence prompt corpus** from:

- official example prompts
- official feature categories
- documented connected-app actions
- published assistant UX patterns
- open-skill design guidance
- observed convergence across assistants

That gives a much more useful artifact for Bond anyway.

---

## What the official docs show

### Microsoft Copilot

Official Microsoft documentation frames Copilot around a few repeated families:

- ask questions
- summarize
- create content
- edit content
- catch up on activity
- search files/work data
- use voice
- use screen/context through Vision
- work across apps and documents

It also explicitly advises prompt structure around goal, context, expectations, and source.

### Siri

Official Apple support continues to center Siri on a narrower but highly practical set of actions:

- get information
- call, text, email
- music/podcasts playback control
- control device settings and smart home devices
- navigation and ETA
- app actions
- reminders, timers, alarms, calendar-related tasks
- contextual follow-up with Apple Intelligence

### Gemini on Android / mobile

Official Gemini documentation emphasizes:

- text, voice, image, camera interaction
- writing and editing help
- summarize/explain/reformat
- ask about current screen or current page
- event creation and calendar management
- calling and messaging through connected apps
- smart-home control
- app-connected actions with permission boundaries
- multimodal context

### Mycroft

Mycroft’s official docs and skill design guidance highlight classic voice-assistant families:

- timers, alarms, weather, time/date
- factual Q&A
- music/podcasts
- news
- smart home
- games
- installable/updatable skills
- intent-driven design rather than arbitrary command strings

---

## The real pattern behind assistant usage

Across official docs and example ecosystems, the practical assistant workload clusters into a surprisingly stable set of families.

### The real “top use cases” are not 100 unrelated prompts

They are recurring families:

1. communication
2. reminders and calendar
3. media playback and control
4. factual Q&A
5. writing/editing/summarization
6. navigation and places
7. device/app control
8. screen/context help
9. smart-home actions
10. search and retrieval
11. shopping/simple tasks/lists
12. lightweight automation and handoff

That means Bond does **not** need 100 disconnected tricks.
It needs strong support for the top 10–12 task families, with enough prompt coverage to generalize naturally.

---

## Synthetic “Top 100 prompt corpus” for capability planning

This is **not** a claim of exact market ranking.
It is a planning corpus derived from official examples and dominant assistant task families.

Its purpose is to teach the capability planner what users are likely to ask in practice.

## Group A — information and quick answers

1. What’s the weather today?
2. What time is it in another city?
3. What’s on my calendar today?
4. What’s my next event?
5. What is this word?
6. Translate this sentence.
7. Summarize this topic.
8. Explain this simply.
9. Compare these two things.
10. Give me a quick overview of this subject.

## Group B — reminders, timers, alarms, routines

11. Set a timer for 10 minutes.
12. Set an alarm for tomorrow morning.
13. Remind me to do something at a time.
14. Remind me when I get home.
15. Remind me when I leave work.
16. Show my reminders.
17. Edit that reminder.
18. Cancel that timer.
19. Snooze the alarm.
20. Start a daily routine/reminder.

## Group C — calendar and scheduling

21. Create an event for tomorrow.
22. Move my meeting.
23. What meetings do I have this week?
24. Add this to my calendar.
25. Find free time this afternoon.
26. Schedule a collaboration meeting.
27. Show details for that event.
28. Edit the location of my event.
29. Cancel the event.
30. Tell me what changed on my calendar.

## Group D — communication

31. Send a text to a contact.
32. Call a contact.
33. Draft an email reply.
34. Summarize my unread email.
35. Congratulate someone by email.
36. Message someone on a connected app.
37. Read my last message.
38. Rewrite this message to sound better.
39. Make this email more formal.
40. Create subject line options.

## Group E — writing, editing, summarization

41. Summarize this document.
42. Rewrite this paragraph.
43. Fix the grammar in this text.
44. Turn these notes into bullets.
45. Turn this into an email.
46. Turn this into a report outline.
47. Create a presentation outline.
48. Shorten this text.
49. Make this more diplomatic.
50. Extract action items from this content.

## Group F — search, retrieval, catch-up

51. What changed recently?
52. What did I miss in the meeting?
53. Summarize the web page on screen.
54. Search my files for a topic.
55. Find the latest from a person/project.
56. Show me the relevant document.
57. Find notes from last week.
58. Compare these sources.
59. Get the key points from this repository.
60. Catch me up on this topic.

## Group G — device and app actions

61. Open the browser.
62. Open a website.
63. Open my downloads folder.
64. Show this file in file manager.
65. Launch a specific app.
66. Switch audio output.
67. Change volume.
68. Toggle do-not-disturb.
69. Show Bluetooth settings.
70. Open Wi-Fi settings.

## Group H — media and entertainment

71. Play music.
72. Pause playback.
73. Skip this track.
74. Resume the podcast.
75. Lower the volume.
76. Find a song.
77. What song is this?
78. Open a video app.
79. Play news headlines.
80. Continue what I was listening to.

## Group I — navigation, places, practical daily help

81. Give me directions to a place.
82. Share my ETA.
83. Find a nearby store.
84. Find a nearby pharmacy.
85. Show places on the map.
86. What’s the traffic like?
87. Where did I park?
88. Find a restaurant nearby.
89. Plan a short trip.
90. Help me build an errand route.

## Group J — smart environment and contextual help

91. Turn on the lights.
92. Turn off a device.
93. Adjust thermostat/smart-home control.
94. Ask about what’s on my screen.
95. Ask about what’s in this photo.
96. Help me with the app I’m looking at.
97. Walk me through a task step by step.
98. Tell me what this setting means.
99. Help me do this in the current app.
100. Continue from the previous context.

---

## Strategic implication for Bond

Bond does not need to mimic commercial assistants feature-for-feature.

It does need to cover the same **capability families**, especially the ones that matter on local-first systems:

- local file and app actions
- environment inspection
- notes/reminders/task handoff
- search and summarization
- web/file/repo research
- desktop integration
- communication handoff
- contextual help
- media/device basics

That is where utility lives.

---

## Capability doctrine for Bond

## Design principle

Bond should expose capabilities in this order of preference:

1. deterministic and read-only
2. deterministic and rootless with explicit user intent
3. rootless interactive handoff through standard platform APIs
4. rootless write actions with confirmation
5. privileged actions only in a distinct, explicit lane

This ordering matters more than “how many commands it supports.”

---

## The capability model Bond should adopt

Bond should move to a formal capability registry, conceptually like this:

```yaml
capabilities:
  open_uri:
    class: handoff
    risk: low
    read_only: false
    rootless: true
    confirmation: false
    adapters:
      linux: xdg_open_or_portal
      macos: nsworkspace
      windows: shell_open
      android: intent_open
  scan_system_profile:
    class: inspection
    risk: low
    read_only: true
    rootless: true
    confirmation: false
    adapters:
      linux: linux_system_probe
      macos: macos_system_probe
      windows: windows_system_probe
      android: android_system_probe
  compose_email:
    class: communication
    risk: medium
    read_only: false
    rootless: true
    confirmation: true
    adapters:
      linux: portal_email_or_mailto
      macos: mail_handoff
      windows: mail_handoff
      android: intent_send
```

The exact schema can differ, but the design requirement should not.

---

## Rootless-first architecture for capabilities

## What “rootless first” should mean in Bond

It should mean all of the following:

- no default assumption of administrative access
- no default mutation of system-wide config
- no reliance on `/etc` or privileged service changes for ordinary tasks
- prefer user-space APIs, user session state, XDG user dirs, desktop handlers, portals, and app handoff
- prefer user-level background services/timers where persistent automation is needed
- privilege escalation is never implicit

## Why this matters

A local assistant that requires privilege too often becomes:

- dangerous
- brittle
- desktop-specific
- hard to package
- hard to trust
- hard to port

Rootless-first is not just a safety posture.
It is also a portability posture.

---

## System detection: what Bond should know, and in what order

Bond needs a more rigorous hierarchy of system facts.

## Layer 0 — immutable or near-authoritative OS facts

These should be the first facts collected and normalized.

### Linux

- OS identity from `os-release`
- kernel family/version
- architecture
- hostname class
- session type
- desktop environment/session
- current user identity
- home directory
- XDG user directories
- PATH-resolved executable presence
- user/systemd availability
- desktop-entry/default-handler information
- portal availability and portal backend presence

### Windows

- OS identity and version
- edition/build
- architecture
- user identity
- shell/session environment
- installed app/package query availability
- default browser/default handlers when accessible
- app package visibility
- available automation surfaces

### macOS

- OS version
- architecture
- hardware model summary
- current user identity
- default browser / default app resolution
- installed app visibility
- automation permission boundaries
- GUI/session state

### Android

- OS version / API level
- manufacturer / device class
- supported assistant intents or app integrations
- default assistant role
- package visibility constraints
- permission status for relevant assistant surfaces
- available connected apps
- foreground context limits

## Layer 1 — user-environment facts

These are more changeable and should be refreshed periodically.

- default browser
- default mail app
- default file manager
- default terminal
- default editor
- installed browsers/editors/media players
- clipboard availability
- notification capability
- available calendars/notes/task backends
- installed package formats and managers
- portal support
- available D-Bus/session bus
- smart-home integrations if configured

## Layer 2 — assistant-usable facts

These are not raw scan results.
They are derived assistant truths such as:

- “can open URLs safely”
- “can present file chooser through portal”
- “can compose email via portal or mailto handoff”
- “can enumerate desktop apps”
- “can launch GUI apps in current session”
- “can read clipboard”
- “can show notifications”
- “can inspect installed Flatpak apps”
- “can create user-scoped timers”
- “cannot safely mutate system network config without privilege”

This is the layer the model should see.

---

## Linux capability architecture Bond should target first

Because Bond is Linux-first right now, the Linux capability stack should be the canonical baseline.

## 1. Detection sources Bond should treat as primary on Linux

### A. `os-release` and related identity data

This should be the canonical base for distro identity, not hand-written distro assumptions.

### B. session and desktop facts

Use environment and desktop/session APIs to determine:

- DE/WM
- X11 vs Wayland
- DBus session presence
- graphical availability
- current user scope

### C. XDG user directories

These should remain the source of truth for localized user folders.

### D. Desktop Entry and handler data

Bond should use desktop entries and default handlers as first-class data, not merely shell guesses.

This is how it should understand:

- which app owns a URI scheme
- which app opens mailto/http/https
- what desktop files correspond to visible apps
- how to hand off actions safely

### E. XDG Desktop Portal

For rootless, desktop-neutral, and future-sandboxed integration, portals are extremely important.

At minimum, Bond should plan around portal-backed or portal-aware capabilities for:

- file chooser
- opening URIs
- sending email
- printing
- notifications and related host interaction where relevant
- future-safe desktop interoperability

### F. D-Bus and session services

On Linux, many assistant-friendly capabilities are better modeled as desktop/session services rather than raw commands.

Bond should not require deep D-Bus expertise from the model.
It should wrap D-Bus/session functionality behind adapters.

### G. user-level systemd

For periodic background maintenance and assistant-owned recurring jobs, user-level services/timers are the right rootless pattern on systemd systems.

This fits Bond’s existing timer/service direction and should become part of the capability plan rather than a one-off implementation detail.

---

## Linux command support: what “support most Linux commands” should really mean

The user goal says Bond should be able to use most Linux commands.

That statement needs correction.

Bond should **not** try to become a generic shell surrogate.
That is the wrong abstraction.

The correct objective is:

> Bond should understand and safely expose the major capability classes that Linux users normally reach through commands.

That leads to a better architecture.

## The command families Bond should cover conceptually

### Read-only inspection

- system identity
- hardware summary
- storage summary
- memory summary
- network summary
- process/service status
- package/app presence
- desktop/session facts
- filesystem metadata
- logs within allowed scope
- environment variables and runtime context

### File operations

- open
- reveal/show in folder
- copy/move/rename within allowed scope
- archive/extract within allowed scope
- search files by name/content
- inspect file type/metadata
- preview text/image/media metadata

### App and desktop actions

- launch app
- open specific file/URL with default app
- hand off to mail/browser/map/player
- notification display
- clipboard read/write where allowed
- screenshot or screencast handoff where supported
- settings page handoff

### Communication handoff

- compose email
- open chat/web messaging target
- hand off to calendar creation
- export/share file through app

### Network and web assistance

- resolve connectivity status
- detect active network context
- open web resources
- perform assistant-owned search/research flows
- summarize current page or selected content

### Developer / power-user support

- inspect repo state
- inspect project files
- search docs/code
- summarize logs
- explain errors
- draft patches or plans
- run bounded tools in safe lanes

### Automation / routine support

- user reminders
- periodic checks
- recurring summaries
- notebook/report generation
- user-scoped background jobs

### Media and environment

- playback control
- volume control
- device output switching where supported
- smart-home integration through explicit adapters
- basic now-playing or current-context awareness

This is a capability map, not a command dump.
That is the right level.

---

## Cross-platform branching model Bond should adopt

Bond should not grow one code path with scattered platform checks.
It should adopt a branching model like this:

```text
intent
→ capability resolution
→ policy check
→ host capability registry lookup
→ adapter selection
→ execution or handoff
→ structured result
```

## Example

User asks:
“Open this site in my browser.”

Bond should do:

1. classify as `open_uri`
2. confirm URI/target
3. inspect host capability registry
4. choose best adapter:
   - Linux desktop: portal/OpenURI or desktop handler
   - macOS: workspace/open
   - Windows: shell/default handler
   - Android: intent open
5. execute handoff
6. return structured result

Not:
“Maybe run browser-specific command X.”

---

## Recommended adapter families

## Linux adapters

Bond should plan Linux adapters in this order of preference.

### 1. standards-based desktop/session adapters

Use:
- XDG handlers
- desktop entries
- XDG portals
- user dirs
- D-Bus session services
- user-level systemd for recurring user jobs

This is the most portable Linux layer.

### 2. distro/desktop-specific enrichments

For example:
- Cinnamon-specific settings integration
- Nemo-specific reveal/open behavior
- Flatpak-aware launching or metadata
- Snap-aware visibility
- Wayland/X11 nuance handling

These should be optional enrichments, not the base contract.

### 3. bounded shell-backed fallbacks

When no better interface exists, Bond may use shell-level tools, but only behind typed adapters and only when policy allows it.

The model should never speak raw shell as its primary language.

## Windows adapters

Primary families should be:

- PowerShell / CIM / WMI for structured system facts
- Shell/default handler APIs for open/handoff
- package query surfaces for installed apps
- Windows notification/app action surfaces if ever added
- user-scoped tasking/automation before machine-wide changes

## macOS adapters

Primary families should be:

- workspace/default-app APIs
- system information surfaces
- Apple-supported system settings/app handoff surfaces
- user-scoped automation and app interaction first
- permission-aware automation boundaries

## Android adapters

Primary families should be:

- Intents and role-based assistant/app handoff
- connected-app integrations
- package visibility within Android restrictions
- permission-aware capability exposure
- assistant actions centered on communication, notes, reminders, camera/context, and app invocation

---

## Minimum viable capability matrix Bond should target

The right target is not “everything.”
It is a strict matrix of high-value capabilities.

## Tier 1 — essential, high-utility, rootless, low/medium risk

These should be prioritized first.

### Inspection and grounding

- host identity summary
- session/desktop summary
- default apps summary
- installed app inventory summary
- current path and user-dir resolution
- package ecosystem summary
- portal availability summary
- calendar/notes/task backend presence
- clipboard/notification availability
- current capability registry export

### Safe handoff actions

- open URI
- open file with default app
- reveal file in file manager
- launch app by known desktop/app identity
- compose email
- open calendar event creation handoff
- open notes/task app target
- open settings targets
- show notification

### Research and context actions

- summarize current page/text/file
- search repository/docs/local notes
- compare sources
- catch up on recent changes
- explain current system state

### User productivity actions

- create reminder through supported backend
- create timer/alarm if backend exists
- create note
- extract TODOs from text
- turn text into structured output

## Tier 2 — valuable but desktop/backend dependent

- clipboard read/write
- screenshot or screencast context
- media playback control
- now-playing inspection
- smart-home integration
- file chooser/save dialog through portals
- print handoff
- app-specific actions
- developer assistant tool execution in bounded lanes

## Tier 3 — later, careful expansion

- cross-device sync
- deeper automation flows
- complex multi-app transactions
- machine-wide settings mutation
- package install/update/uninstall assistance
- privileged service/network/storage modifications

---

## Capability registry design recommendation

Bond should add a formal capability registry with at least these dimensions:

```yaml
name:
domain:
class:
description:
read_only:
side_effects:
rootless:
interactive:
needs_gui_session:
needs_network:
needs_user_confirmation:
needs_elevated_lane:
platforms:
backends:
preferred_backend_by_platform:
degraded_modes:
result_schema:
error_schema:
audit_tag:
```

## Why this matters

Without this registry, the model will improvise.

With this registry, the model can answer correctly:

- “I can do this directly.”
- “I can hand this off to your default app.”
- “I can inspect this but not change it.”
- “I can only do this on Linux desktop.”
- “I need confirmation for this.”
- “This requires the privileged lane.”
- “This action is unsupported on the current host.”

That is what makes an assistant feel truthful.

---

## Result schema recommendation

Every action should return typed results, not prose blobs.

Example:

```json
{
  "ok": true,
  "capability": "open_uri",
  "backend": "xdg_portal_openuri",
  "platform": "linux",
  "interactive": true,
  "side_effects": ["launch_default_browser"],
  "detail": {
    "uri": "https://example.org"
  }
}
```

Example failure:

```json
{
  "ok": false,
  "capability": "compose_email",
  "backend": null,
  "platform": "linux",
  "error_code": "no_supported_email_backend",
  "reason": "No portal email interface and no default mail handler could be resolved safely.",
  "retryable": false
}
```

This matters because the assistant layer should reason over structured outcomes, not vague strings.

---

## How Bond should think about “tools”

Bond should define tools in four classes.

## Class 1 — inspectors

Read-only, deterministic, safe.
Examples:

- system probe
- file metadata probe
- app inventory probe
- environment probe
- capability registry probe

## Class 2 — handoff tools

Open something or delegate to the user’s chosen app/backend.
Examples:

- open URI
- reveal file
- compose email
- create calendar draft
- print dialog
- file chooser

## Class 3 — bounded mutators

Write within a safe, well-defined, rootless scope.
Examples:

- create note in designated store
- write a project file in allowed tree
- save a generated report
- append reminder/task entry in chosen backend

## Class 4 — privileged lane tools

Clearly separate lane.
Examples:

- modify machine-wide configuration
- service management beyond user scope
- network reconfiguration
- package management
- protected path mutation

The normal assistant should speak to Classes 1–3 first.
Class 4 should remain exceptional.

---

## Proposed system-fact schema

Bond should export system facts into a normalized schema that distinguishes levels of certainty.

Example structure:

```yaml
host:
  platform: linux
  distro:
    id: linuxmint
    version_id: "22.3"
    source: authoritative
  kernel:
    value: ...
    source: authoritative
  session:
    type: x11
    desktop: cinnamon
    source: mixed
  default_apps:
    browser:
      desktop_id: firefox.desktop
      source: authoritative_handler
    mail:
      desktop_id: thunderbird.desktop
      source: authoritative_handler
  app_inventory:
    browsers:
      - firefox
      - chromium
    source: derived
  portals:
    open_uri: available
    email: available
    file_chooser: available
    source: authoritative_runtime_probe
assistant_usable_capabilities:
  open_uri: supported
  compose_email: supported
  print_dialog: supported
  clipboard_read: unsupported
```

This is far superior to a flat scan dump.

---

## Recommended implementation phases

These phases are about capability and tool architecture only.
They deliberately do not redesign the brain/router.

## Phase 1 — harden system truth and capability truth

### Goal

Turn current scanning into a reliable capability substrate.

### Deliverables

- normalized host profile schema
- confidence/source labels for each fact
- explicit capability registry
- derived assistant-usable capability layer
- separation between raw scan and assistant-facing truths
- refresh policy for dynamic vs static facts

### Why first

Without this, all later capabilities rest on guesswork.

## Phase 2 — build rootless handoff layer

### Goal

Make Bond useful without risky mutation.

### Deliverables

- open URI/file/app
- reveal in file manager
- compose email
- calendar/note/task handoff
- notification handoff
- print/file-dialog handoff where available
- platform adapter boundaries

### Why second

This gives immediate real-world usefulness while preserving safety and portability.

## Phase 3 — build typed bounded mutators

### Goal

Allow safe assistant-authored changes in clearly bounded scopes.

### Deliverables

- note creation
- report export
- project-file writing within allowed trees
- structured reminder/task creation
- bounded content transformation to files
- clearer confirmation semantics

### Why third

Now Bond can do useful work, not just inspect or hand off.

## Phase 4 — desktop context and media improvements

### Goal

Increase convenience and “assistant feel.”

### Deliverables

- clipboard
- screenshot/page/context summary inputs
- media playback control
- now-playing/context awareness
- richer current-app/current-page support where feasible
- desktop-specific enrichments

### Why fourth

Useful, but less foundational than truth/policy/handoff.

## Phase 5 — cross-platform adapter expansion

### Goal

Prepare the architecture for non-Linux hosts without breaking Linux quality.

### Deliverables

- Windows adapter baseline
- macOS adapter baseline
- Android adapter baseline
- capability parity matrix
- unsupported/degraded-mode contracts

### Why fifth

Portability before architecture maturity usually creates mess.
Portability after adapter contracts creates leverage.

## Phase 6 — privileged lane expansion

### Goal

Explicitly and narrowly support high-consequence actions.

### Deliverables

- privileged lane contracts
- confirmation UX
- audit schema
- elevated capability registry entries
- stricter policy gate integration
- refusal rules and safer fallback suggestions

### Why last

If this comes early, the system becomes dangerous and incoherent.

---

## Recommended priority order for actual usefulness

If the goal is practical usefulness soon, the order should be:

1. capability registry
2. authoritative/default app detection
3. rootless handoff actions
4. local search/summarize around files/pages/notes
5. reminders/notes/task backends
6. app launch and reveal/open flows
7. notifications/clipboard/context
8. media and smart environment
9. cross-platform adapters
10. privileged lane expansion

This is the order that produces utility without making the system reckless.

---

## Specific recommendations for the current codebase

## 1. Split scanning from interpretation

Current scan logic should produce raw facts.
A second stage should interpret those facts into assistant-usable capabilities.

Do not mix them.

## 2. Replace “binary exists” with ranked evidence

For things like browser/editor/file manager, Bond should rank evidence:

1. explicit default handler
2. desktop/session API fact
3. desktop entry match
4. installed binary presence
5. heuristic fallback

This is much stronger than current likely/default guesses.

## 3. Add a capability registry module

This should become the machine-readable source of truth for:
- what capabilities exist
- which backends implement them
- which platform they support
- which policy level applies

## 4. Add adapter modules by domain, not by one giant executor

Examples:
- `cap_open.py`
- `cap_email.py`
- `cap_calendar.py`
- `cap_notes.py`
- `cap_notifications.py`
- `cap_files.py`
- `cap_media.py`
- `cap_probe_linux.py`
- `cap_probe_windows.py`
- `cap_probe_macos.py`
- `cap_probe_android.py`

Exact names can differ, but the split should be capability-first.

## 5. Keep shell/backend details behind adapters

The assistant should request `compose_email`, not “use mailto” or “call xdg-email.”
Implementation detail should stay below the contract line.

## 6. Add degraded-mode responses

For every capability, Bond should be able to say:

- supported directly
- supported via handoff
- supported in reduced form
- unsupported on this host
- supported only in privileged lane

That prevents hallucinated certainty.

## 7. Make “current app/page/screen context” explicit and optional

Commercial assistants increasingly use current-screen context.
Bond should plan for this, but not fake it.

The capability must explicitly indicate whether Bond currently has:
- no screen context
- selected-text context
- current-page context
- screenshot/image context
- app/window context

That should be modeled, not implied.

## 8. Model confirmation semantics centrally

Some actions should always need confirmation.
Some should never.
Some need confirmation only when parameters are inferred rather than explicit.

This logic belongs in policy/capability metadata, not scattered through action handlers.

---

## Cross-platform planning guidance

## Linux

Linux should remain the reference platform first.

Bond should be strongest here in:
- system inspection
- file/app handoff
- project/repo assistance
- desktop-aware local actions
- rootless user-scoped automation

## Windows

Windows support should not begin with “port every Linux command.”
It should begin with:
- system fact adapters via CIM/WMI/PowerShell surfaces
- default app/open/handoff
- package/app inventory
- user-scoped tasking and common actions
- file/app interaction
- bounded developer support

## macOS

macOS support should prioritize:
- system identity
- default app resolution
- app launching and file/URL handoff
- user-scoped workflows
- permission-aware boundaries
- desktop-friendly contextual assistance

## Android

Android support should be narrower and more opinionated:
- communication
- reminders/tasks/calendar
- web/page/screen summaries where available
- app invocation through intents
- camera/image-based assistance
- connected-app handoff
- phone-centric productivity

Trying to make Android behave like desktop Linux would be a mistake.

---

## Non-goals for this phase

The following should **not** be treated as primary capability work right now:

- router/brain redesign
- voice-first UX redesign
- Cinnamon applet redesign
- full packaging discussion
- full autonomous agent orchestration
- broad package management and system mutation
- “support every shell command”
- fake parity with Siri/Gemini/Copilot marketing checklists

Those are distractions unless the capability substrate is correct first.

---

## Acceptance criteria for a serious capability layer

Bond’s capability work should not be considered mature until all of the following are true:

### Truthfulness
- The assistant can accurately state what it can and cannot do on the current host.

### Determinism
- Common capability decisions do not depend on model improvisation.

### Rootless usefulness
- A large set of useful actions work without privilege.

### Structured outcomes
- Every tool/action returns typed results and typed failures.

### Portability
- Linux-specific details are isolated behind adapters.

### Degraded handling
- Unsupported or partial scenarios are reported explicitly.

### Confirmation discipline
- Side-effecting actions follow central confirmation rules.

### Host awareness
- Default apps, user dirs, session type, and available backends are known with source confidence.

### Expandability
- New OS or desktop support can be added by implementing adapters rather than rewriting the assistant core.

---

## Final recommendation

Bond should improve its capabilities by becoming less command-like and more contract-driven.

The winning design is:

- **scan less randomly**
- **classify facts better**
- **formalize capabilities**
- **prefer rootless standards**
- **wrap platform differences behind adapters**
- **return structured results**
- **expand high-value families first**
- **keep privilege as a separate lane**

The short version is:

> Bond should not aim to “know most commands.”
> It should aim to expose most useful assistant capabilities through deterministic, portable, policy-aware contracts.

That is what will make it genuinely useful rather than merely impressive in demos.

---

## Source notes used for this analysis

These source notes are included so another LLM can understand the external grounding behind the planning direction.

### Official assistant capability references

- Microsoft Support and Microsoft Windows pages describing Copilot prompt structure, content creation, summarization, catch-up flows, app/file grounding, Copilot Voice, and Copilot Vision
- Apple iPhone User Guide and Apple support pages describing Siri for information, communications, media, device/smart-home control, navigation, app actions, reminders, and Apple Intelligence follow-up context
- Google Gemini and Pixel help pages describing Gemini on Android/mobile, connected apps, multimodal input, current-screen/page help, calendar management, WhatsApp calling/messaging, permissions, and device-assistant behavior
- Mycroft official skill and VUI design documentation describing timers, alarms, weather, factual Q&A, media, news, smart home, and skill-based expansion

### Official Linux/desktop integration references

- `os-release` and related system identity documentation
- freedesktop Desktop Entry Specification
- XDG Desktop Portal documentation and API reference, especially OpenURI, FileChooser, Email, and Print
- D-Bus and systemd documentation relevant to rootless user-session capability patterns

### Official cross-platform references

- Microsoft Learn documentation for Windows system information through CIM/WMI and app/package query surfaces
- Apple documentation for workspace/default-app behavior and Mac system information surfaces

