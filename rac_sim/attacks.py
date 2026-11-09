"""Malicious-agent behaviours.

An adversary runs the honest update internally (so it behaves normally until `at`), then
rewrites what it broadcasts. The model sends the SAME message to every out-neighbor.
transform(honest_msg, k) returns the message to send (or None for silence) for Phi_i[k].
"""
from __future__ import annotations

import random
from dataclasses import replace

from .agent import Phi


class Attack:
    # False: the paper's "malicious" model, one message `transform(msg, k)` is sent to every
    # out-neighbor. True: Byzantine, `transform_to(msg, k, recipient)` is called per recipient.
    equivocates = False

    def __init__(self, at: int):
        self.at = at                 # first k for which the broadcast Phi_k is corrupted

    def active(self, k: int) -> bool:
        return k >= self.at

    def transform(self, msg: Phi, k: int):
        return msg

    def transform_to(self, msg: Phi, k: int, recipient: int):
        return self.transform(msg, k)

    def tamper_inbox(self, inbox: dict, k: int) -> dict:
        """Lets the adversary change what it *claims* to have received before its honest
        update runs. Default: no change."""
        return inbox

    def filter_detections(self, found: set, k: int) -> set:
        """Adversaries run the honest detector internally; this lets them hide detections."""
        return found


class Crash(Attack):
    """Goes silent."""
    def transform(self, msg, k):
        return None if self.active(k) else msg


class Offset(Attack):
    """Inflates its running sums by a constant, i.e. injects fake mass once."""
    def __init__(self, at, dy=5.0, dz=0.0):
        super().__init__(at)
        self.dy, self.dz = dy, dz

    def transform(self, msg, k):
        if not self.active(k):
            return msg
        ly, gz = msg.own_next
        return replace(msg, own_next=(ly + self.dy, gz + self.dz))


class Frozen(Attack):
    """Stops updating: keeps broadcasting the last honest running sums (a 'fixed value')."""
    def __init__(self, at):
        super().__init__(at)
        self._held = None

    def transform(self, msg, k):
        if not self.active(k):
            self._held = msg.own_next
            return msg
        return replace(msg, own_next=self._held)


class TamperInbox(Attack):
    """Pretends in-neighbor `src` sent dy more than it really did, from step `at` on, and then
    runs the honest update on that fake input. Its own update is therefore self-consistent
    (passes the Step 4 reconstruction). Only a node that knows src's true running sum can
    catch it (Step 3): src itself, or a normal common neighbor of src and the attacker.
    With a colluding src this is the paper's 'neighboring malicious agents' case (Lemma 1)."""
    def __init__(self, at, src, dy=5.0):
        super().__init__(at)
        self.src, self.dy = src, dy

    def tamper_inbox(self, inbox, k):
        msg = inbox.get(self.src)
        if not self.active(k) or msg is None:
            return inbox
        ly, gz = msg.own_next
        return {**inbox, self.src: replace(msg, own_next=(ly + self.dy, gz))}


class Equivocate(Attack):
    """Byzantine: from step `at`, misbehaves ONLY toward the recipients in `offsets`
    ({recipient: (dy, dz)} or {recipient: dy}); every other out-neighbor gets the honest message.
    The corrupted message adds (dy, dz) to the broadcast running sums. `repeat=False` corrupts
    only message `at`, `repeat=True` every message from `at` on."""
    equivocates = True

    def __init__(self, at, offsets, repeat=False):
        super().__init__(at)
        self.offsets = {r: (v if isinstance(v, tuple) else (v, 0.0)) for r, v in offsets.items()}
        self.repeat = repeat

    def transform_to(self, msg, k, recipient):
        hit = (k >= self.at) if self.repeat else (k == self.at)
        if not hit or recipient not in self.offsets:
            return msg
        dy, dz = self.offsets[recipient]
        ly, gz = msg.own_next
        return replace(msg, own_next=(ly + dy, gz + dz))


class Conceal(Attack):
    """Protects colluders: never detects (and so never reports or removes) the IDs in
    `protect`. Combined with a colluder that injects mass, it passes the bad mass on while
    staying self-consistent. Only claim checks (1a/1b) can catch it."""
    def __init__(self, protect, at=0):
        super().__init__(at)
        self.protect = set(protect)

    def filter_detections(self, found, k):
        return set(found) - self.protect if self.active(k) else found


class FakeDetection(Attack):
    """Reports an honest node as detected (tries to get it isolated). Caught by Step 1."""
    def __init__(self, at, victim):
        super().__init__(at)
        self.victim = victim

    def transform(self, msg, k):
        if not self.active(k):
            return msg
        return replace(msg, A=msg.A | {self.victim})


class RandomLie(Attack):
    def __init__(self, at, scale=3.0, seed=0):
        super().__init__(at)
        self.rng, self.scale = random.Random(seed), scale

    def transform(self, msg, k):
        if not self.active(k):
            return msg
        ly, gz = msg.own_next
        return replace(msg, own_next=(ly + self.rng.uniform(-self.scale, self.scale), gz))
