# Voice Layer

Voice is optional and later. The text path remains canonical.

## Voice pipeline

The intended pipeline is:

1. wake or push-to-talk
2. local STT
3. text normalization
4. standard Bond text pipeline
5. response text
6. optional TTS

## Component selection status

Vosk and Piper are provisional candidates only.

Before committing, benchmark options for:

- resource use
- latency
- packaging pain
- Greek and English quality

## Behavior and safety contract

Voice must not bypass:

- text behavior contract
- policy layer
- capability registry
- safety controls

Greek text support is not blocked by voice.

## Runtime documentation to define later

Future implementation docs should define:

- enable/disable model
- runtime footprint
- device permissions
- fallback behavior

## Current implementation status

Voice is planned and not yet complete.

## Cross references

- `docs/BEHAVIOR_CONTRACT.md`
- `docs/CAPABILITIES.md`
- `docs/SERVICE.md`
- `docs/RELEASE_PROCESS.md`
