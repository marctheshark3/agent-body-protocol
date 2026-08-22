---
title: "Lamp Optical Peer Channel - Plan"
type: feat
date: 2026-08-22
topic: lamp-optical-peer
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
product_contract_source: ce-brainstorm
execution: code
---

# Lamp Optical Peer Channel - Plan

## Goal Capsule

- **Objective:** A lamp in the room may speak to another lamp the way people speak: line of sight, observable, rate-limited. The online lamp may hand a sealed artifact or a nine-event chirp to an offline lamp. It cannot take camera, mic, or servos. Leftover stays dead.
- **Product authority:** Companion protocol in `agent-body-protocol`. Extends custody + vendor. Creature-bus already locked one language and two channels. This adds a third physical medium, not a new language.
- **Open blockers:** None for the kernel. Live IR/LED PHY is later. Lamp has 64 WS2812 today and no IR transceiver in the BOM.
- **Stop:** Do not invent a new robot language. Do not let a networked lamp become leftover eyes. Do not treat IR as telepathy over MQTT. Do not drive another body's servos.
- **Execution:** code. In-repo peer double plus tests. Optical PHY later.

## Product Contract

### Summary

Robots talk in the room. Humans can see it.
The online lamp is a gateway for sealed software and nine events.
It is not a backdoor into the offline lamp's house.

### Problem Frame

Sebastian's IR idea is the human analog: speech, not telepathy.
A lamp that just arrived, not on Wi-Fi, still needs a way to get a signed build or a local event from the lamp that is already home.
If that path carries camera or remote drive, F1 is a costume again — leftover dies, then the neighbor lamp reopens the house.
Creature-bus already said wire is truth and chirps are a render. IR/LED is another PHY for the same nine events.
Visible LED is the honest first PHY: the owner can see them talking. IR is quieter bandwidth later, same policy.

### Key Decisions

- **One language.** Nine ABP events. No new robot-to-robot verbs.
- **Three media, one policy.** `wire`, `led`, `ir` are interchangeable at the custody gate.
- **Peer is a channel, not a served seat.** Owner still has house keys. Peer cannot be bound as owner by showing up.
- **Sealed artifacts only.** An offline lamp applying a build from a peer uses the vendor rule: signed or refuse, freeze wins, leftover stays closed.
- **No sensors across bodies.** Peer cannot pull camera, mic, or servos. Gateway cannot see the other house.
- **Visible first.** 64 WS2812 already exists. IR transceiver is not in the lamp BOM. Do not claim live IR.
- **Not leftover.** A stranger lamp in the room is a peer offer, not an installer session.

### Actors

- A1. **Owner** of each body — still has that body's camera, mic, servos.
- A2. **Online lamp** — may offer a sealed artifact or an event over optical.
- A3. **Offline lamp** — may accept the offer under the same vendor/custody rules.
- A4. **Expired installer** — cannot ride the optical path back in.
- A5. **Judge** — watches an IR/LED offer that is not a camera grant.

### Key Flows

- F1. Event over optical
  - **Trigger:** Online lamp offers `tests_passed` over `led` or `ir`.
  - **Outcome:** Offline lamp accepts the event. Leftover still closed. No servo grant.
- F2. Sealed artifact over optical
  - **Trigger:** Online lamp offers a signed build. Owner has not frozen.
  - **Outcome:** Apply. Leftover still closed. Vendor pull of camera still denied.
- F3. Sensor offer refused
  - **Trigger:** Online lamp asks for camera, mic, or servos.
  - **Outcome:** Deny + receipt. Same class as vendor pull.
- F4. Unsigned artifact refused
  - **Trigger:** Peer offers an unsigned build after handoff.
  - **Outcome:** No apply. Frozen signed builds also refuse.

### Requirements

- R1. Peer offers are `event` or `artifact`. Sensor kinds refuse.
- R2. Events must be one of the nine ABP names.
- R3. Media must be `led`, `ir`, or `wire`. Policy is identical.
- R4. Artifact apply reuses the sealed vendor rule. Leftover cannot reopen.
- R5. A prompt cannot grant a sensor pull.
- R6. Receipts name the media and kind, not household identity.
- R7. Peer is not a presence subject that gets served like owner.

## Planning Contract

U1. `custody/peer.py` accept/refuse.
U2. Tests: event ok, sensor deny, signed artifact, leftover stays closed, IR and LED same.
U3. Demo beat: peer LED event + peer camera deny after vendor apply.

## Success Criteria

- A judge can watch a peer offer that is not a camera grant.
- Slice fails if an optical path reopens leftover or serves a peer as owner.
- Do not claim a live IR PHY from this kernel.
