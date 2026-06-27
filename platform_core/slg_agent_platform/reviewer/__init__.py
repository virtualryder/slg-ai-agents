"""Human-approval reviewer service — the production replacement for the mint_approval.py stand-in.

The smoke-test stand-in minted a bound approval token from a script that had to hold the
token secret. That is fine for a dev smoke run but is NOT a real control: anyone with the
secret could approve anything. This package is the real service: an authenticated reviewer
(verified JWT) approves or rejects a SPECIFIC pending request; the service checks the
reviewer's authority + separation of duties, mints the bound token SERVER-SIDE (the reviewer
never sees the secret), resumes the paused Step Functions execution, and writes the decision
to the append-only audit. Single-use is enforced by a conditional state transition on the
pending record so an approval cannot be replayed.
"""
from .service import ReviewerService, ReviewerError, PendingApproval  # noqa: F401
from .store import InMemoryPendingStore, PendingApprovalStore  # noqa: F401
