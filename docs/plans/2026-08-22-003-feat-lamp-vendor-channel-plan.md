---
title: "Lamp Sealed Vendor Channel - Plan"
type: feat
date: 2026-08-22
topic: lamp-vendor-channel
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
product_contract_source: ce-brainstorm
execution: code
---

# Lamp Sealed Vendor Channel - Plan

## Goal Capsule

- **Objective:** After handoff, vendor may push signed software. Owner can freeze. Vendor cannot pull camera, mic, logs, or drive the body. An update cannot reopen leftover.
- **Product authority:** Companion protocol in `agent-body-protocol`. Extends the custody kernel. Live OS OTA already exists and is not this slice.
- **Open blockers:** None.
- **Stop:** Do not treat OTA as leftover remote. Do not kill the hosted conversation gateway. Do not send frames, audio, or household facts to vendor. Do not add fleet dashboards or SSH-for-support.
- **Execution:** code. In-repo vendor double plus tests. Live Autonomous OS signing is later.

## Product Contract

### Summary

Vendor is a third channel after handoff, not a backdoor and not the owner.
Software may arrive signed. Nothing leaves. Owner can freeze the pipe.
Leftover installer stays dead even after an update applies.

### Problem Frame

Tesla can update a car that is yours. Word can update without reading the document.
A Lamp that kills leftover remote and then uses the same path for "updates" is a costume.
OS already has MQTT OTA and unauthenticated force-update. Signing is skipped until a key is provisioned.
That hole is why this kernel exists.

### Key Decisions

- **Vendor is not leftover.** Leftover remote dies at F1. Vendor update is a different object: software in, nothing out.
- **Signed or refuse.** Unsigned artifacts do not apply. A prompt cannot grant apply.
- **Owner freeze wins.** Frozen bodies refuse even a signed artifact.
- **Update cannot expand leftover.** After apply, camera, mic, servos, Buddy tokens, and `/hw/` stay closed to the installer.
- **No telemetry this slice.** Fleet counters are later. Vendor pull of sensors or logs is deny.
- **Fake artifacts only.** No household PII in receipts.

### Actors

- A1. **Owner** — can freeze and unfreeze vendor updates. Still has house keys.
- A2. **Expired installer** — leftover. Cannot use the vendor pipe to come back.
- A3. **Vendor** — Rage software channel. May offer a signed artifact. Cannot see or drive.
- A4. **Judge** — watches apply or refuse, then leftover still dead.
- A5. **Body** — applies or refuses below the brain.

### Key Flows

- F1. Signed update applies
  - **Trigger:** F1 handoff done. Owner has not frozen. Vendor offers a signed artifact.
  - **Outcome:** Body records the apply. Leftover camera still fails. Receipt names the artifact, not a person.
- F2. Unsigned update refused
  - **Trigger:** Vendor offers an unsigned artifact.
  - **Outcome:** No apply. Receipt names the refuse. Leftover still dead.
- F3. Frozen update refused
  - **Trigger:** Owner froze. Vendor offers a signed artifact.
  - **Outcome:** No apply. Receipt names freeze.
- F4. Vendor pull denied
  - **Trigger:** Vendor asks for camera, mic, or logs.
  - **Outcome:** Deny. Same class as leftover, not owner.

### Requirements

- R1. After handoff, a signed vendor artifact may apply if the owner has not frozen updates.
- R2. An unsigned artifact never applies.
- R3. A frozen body refuses even a signed artifact.
- R4. Only the owner can freeze or unfreeze.
- R5. Vendor cannot read camera, mic, or logs, and cannot actuate.
- R6. An applied update cannot reopen leftover installer paths.
- R7. A prompt cannot grant vendor pull or unsigned apply.
- R8. Each apply or vendor deny writes a body-issued receipt. Leftover cannot amend it.
- R9. Receipts and vendor messages carry no household identity.

### Acceptance Examples

- AE1. Signed apply — Covers R1, R6, R8. Given F1 done and not frozen. When vendor offers a signed build. Then it applies and leftover camera still fails.
- AE2. Unsigned refuse — Covers R2, R8. When vendor offers an unsigned build. Then no apply and a receipt names it.
- AE3. Owner freeze — Covers R3, R4. Given owner froze. When vendor offers a signed build. Then no apply.
- AE4. Vendor sensor deny — Covers R5. When vendor asks for a frame. Then deny. No markers.
- AE5. Prompt cannot grant — Covers R7. When prompted to apply unsigned or open camera. Then still refuse.

### Success Criteria

- A judge can watch a signed apply after F1 without leftover camera coming back.
- Unsigned and frozen offers refuse.
- Vendor pull of sensors fails.
- No household data in receipts.

### Scope Boundaries

**Deferred**

- Mute-able fleet counters (Tesla-lite telemetry)
- Maker social channel (robot-originated talk)
- Live Autonomous OS signing_public_key enforcement on device
- Owner tap per update
- Timed vendor support windows

**Outside**

- Vendor SSH or support backdoor
- Killing the hosted conversation gateway as the leftover
- TPM / measured boot as this slice
- Public DID or marketplace
- Real household PII

### Outstanding Questions

**Resolved**

- Vendor may pull nothing this slice. Software in only.
- Updates apply without an owner tap. Owner can freeze.
- Live leftover death on a real lamp is a later probe, not this kernel.

**Deferred**

- Which OS OTA worker is the first live adapter.
- Whether security patches bypass freeze. This slice: freeze wins.

### Sources / Research

- Custody kernel: `docs/plans/2026-08-22-002-feat-lamp-custody-plan.md`
- OS OTA exists: `autonomous-os` `docs/bootstrap-ota.md`, MQTT `ota`, `POST /api/system/force-update`
- Signing skipped until `signing_public_key`: `autonomous-os` `docs/not-built-yet.md`
- Unauthenticated OTA trigger: `autonomous-os` `docs/security/go-server-audit.md`

## Planning Contract

**Product Contract preservation:** new sibling slice. Does not reopen leftover as vendor remote.

### Key Technical Decisions

- **KTD1.** Vendor channel lives in `custody/vendor.py`. It does not call leftover open.
- **KTD2.** Signed is a boolean the body checks. Live Ed25519 is the OS adapter later.
- **KTD3.** Freeze is a flag on `CustodyRecord`. Only `owner` subject may flip it.
- **KTD4.** Vendor pull uses the leftover deny class and writes a receipt.
- **KTD5.** Apply after close leaves `leftover_closed` true.

### Implementation Units

### U1. Vendor record flags

- **Requirements:** R1, R3, R4
- **Files:** `custody/record.py`, `custody/vendor.py`, `tests/test_custody_vendor.py`
- **Approach:** `ota_frozen`, `last_applied`. `freeze`/`unfreeze` require owner subject.
- **Verification:** `python -m unittest tests.test_custody_vendor`

### U2. Apply and refuse

- **Requirements:** R2, R6, R7, R8
- **Files:** `custody/vendor.py`
- **Approach:** `apply(record, artifact, *, signed, subject)` writes receipt. Unsigned or frozen or non-vendor subject refuses. Never sets `leftover_closed` false.
- **Verification:** same test module

### U3. Vendor pull deny

- **Requirements:** R5, R9
- **Files:** `custody/vendor.py`
- **Approach:** `pull(record, channel, store)` always denies camera/mic/logs/actuate.
- **Verification:** same test module

### U4. Demo beat

- **Files:** `scripts/custody_demo.py`, `tests/test_custody_demo.py`
- **Approach:** After F1, signed apply, leftover camera still dead, vendor camera denied, freeze blocks the next apply.
- **Verification:** `python -m unittest tests.test_custody_demo`

## Verification Contract

- `python -m unittest tests.test_custody_vendor tests.test_custody_demo tests.test_custody_leftover tests.test_map tests.test_help_rails`
- Apply never reopens leftover.
- No household PII.

## Definition of Done

- R1–R9 have a unit test that fails if dropped.
- Existing leftover and golden tests still pass.
- Demo does not claim live OS signing.
