---
name: business-dao-learning
description: "Guide Dao-style learning from real business workflows to transferable first principles. Use when a user wants to understand or design idempotency, state machines, transactions, retries, queues, approvals, payments, inventory, registration, notifications, or cross-system coordination by tracing code and business constraints rather than memorizing framework techniques."
---

# Business Dao Learning

## Overview

Treat an annotation, API pattern, table, queue, or retry setting as a local **shu**, not the final explanation. Derive a Dao only after identifying the business invariant, the durable state that enforces it, and the failure boundaries that constrain it.

Teach interactively. Ask one question that reduces the largest causal uncertainty, wait for the learner's answer, then record a provisional conclusion. Do not turn an unverified implementation detail into a business guarantee.

## Evidence Scope

Read only the evidence needed for the current node:

- API entry point and request identity;
- service state transition and transaction boundary;
- schema constraint, conditional update, or lock that owns an invariant;
- message or remote-call contract; and
- tests, traces, or observability that validate a claim.

Label conclusions as `observation`, `inference`, `convention`, or `hypothesis`. Use virtual identifiers in learning artifacts; do not include patient, payment, or other production-sensitive data.

## Workflow

### 1. Anchor the business result

Name the command, actor, desired result, and prohibited result. Prefer “one effective admission at a time” over “avoid duplicate clicks.” Distinguish repeatable historical actions from one-time active actions.

Ask: “What observable business result would be incorrect if this command arrived twice?”

### 2. State the invariant and its authority

Express the invariant precisely, then find the durable shared state that can enforce it atomically. Separate:

- UX suppression: debounce, repeated-submit filter, or short-lived request lock;
- local correctness: transaction, unique constraint, conditional update, or state-transition guard; and
- cross-system recovery: idempotency key, durable operation record, retry, reconciliation, or compensation.

Do not let an entry-layer filter stand in for a database invariant. Do not apply a uniqueness rule so broadly that it rejects legitimate historical actions.

### 3. Trace failure windows

For every remote side effect, trace these paths:

```text
before local commit -> process crash -> remote success with lost response
-> concurrent duplicate -> delayed retry -> terminal or recoverable failure
```

Explain which work is impossible to roll back across the boundary. If independent systems cannot share an atomic commit, do not promise exactly-once execution from a local transaction.

### 4. Model explicit recovery state

Persist an operation record before or atomically with the local state transition. Model at least `PENDING`, `SUCCEEDED`, `RETRYABLE_FAILED`, and terminal failure when applicable. State which downstream actions are permitted while an external result is pending.

Keep ownership clear: use a guard or unique index for the local invariant; use an operation record for provider, stable business identity, attempts, errors, and outcome. Do not accumulate unrelated provider status columns in a single guard record.

### 5. Build the causal knowledge tree

Create a Mermaid `flowchart TD` with the original business problem, invariant, authority, durable state transition, remote boundary, recovery path, and a boundary or unresolved hypothesis. Keep it under 20 nodes and use causal edge labels.

### 6. Pass the Dao gate

Before proposing implementation, produce all six artifacts:

1. A Dao statement in the form “When [constraint], a system tends to [mechanism] because [reason], trading [cost] for [benefit].”
2. The causal mechanism: identities, state changes, atomic operations, and remaining unavoidable work.
3. Applicability conditions, including the relevant scale or failure assumptions.
4. Falsifiable predictions compared with a naive design.
5. Boundaries and counterexamples.
6. A transfer map covering business intent, stable identity, durable result, side effect, recovery worker, and authority boundary.

If an artifact is missing, continue inquiry. Do not write a project merely because an analogy sounds plausible.

### 7. Transfer and verify

Map the principle to one nearby workflow and one structurally different workflow. For example:

| Role | Admission and insurance | Payment | Message consumer |
|---|---|---|---|
| Stable identity | `admissionId` | `paymentIntentId` | `eventId` |
| Side effect | Insurance registration | Charge | Inventory mutation |
| Durable result | Provider result | Payment result | Inbox record |
| Recovery state | `PENDING` | `PROCESSING` | `PROCESSING` |

Ask the learner to predict the mapping before revealing it unless they request the answer. Build a small simulator, test, or trace only after the Dao gate passes; measure duplicate attempts, accepted results, state transitions, or recovery time.

## Output Shape

Use this compact record at milestones:

```text
Business outcome: <desired and prohibited result>
Evidence: <observation, inference, convention, or hypothesis>
Invariant: <precise business rule and authority>
Failure window: <where local and remote state can diverge>
Recovery state: <pending, success, retryable failure, terminal failure>
Dao: <transferable invariant and tradeoff>
Boundary: <where it fails or cannot be applied>
Next question: <one high-leverage causal question>
```
