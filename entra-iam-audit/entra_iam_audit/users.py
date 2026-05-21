from __future__ import annotations

from datetime import datetime, timezone, timedelta

from .graph_client import GraphClient

USER_SELECT = ",".join([
    "id",
    "displayName",
    "userPrincipalName",
    "mail",
    "accountEnabled",
    "createdDateTime",
    "jobTitle",
    "department",
    "assignedLicenses",
    "signInActivity",
    "userType",
])


def fetch_all_users(client: GraphClient) -> list[dict]:
    return client.get_all(
        "/users",
        params={"$select": USER_SELECT, "$top": "999"},
    )


def get_stale_accounts(users: list[dict], stale_days: int = 90) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=stale_days)
    stale = []
    for user in users:
        activity = user.get("signInActivity") or {}
        last_sign_in = activity.get("lastSignInDateTime")
        if last_sign_in:
            last_dt = datetime.fromisoformat(last_sign_in.replace("Z", "+00:00"))
            if last_dt < cutoff:
                stale.append({**user, "_days_inactive": (datetime.now(timezone.utc) - last_dt).days})
        else:
            # Never signed in — flag if account is older than stale_days
            created = user.get("createdDateTime")
            if created:
                created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                if created_dt < cutoff:
                    stale.append({**user, "_days_inactive": None, "_never_signed_in": True})
    return stale


def get_orphaned_users(users: list[dict], inactive_days: int = 180) -> list[dict]:
    """Users that are disabled but still licensed, or never signed in with a license."""
    orphaned = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=inactive_days)
    for user in users:
        has_license = bool(user.get("assignedLicenses"))
        enabled = user.get("accountEnabled", True)
        activity = user.get("signInActivity") or {}
        last_sign_in = activity.get("lastSignInDateTime")

        reason = None
        if not enabled and has_license:
            reason = "Disabled account with active license"
        elif has_license and last_sign_in:
            last_dt = datetime.fromisoformat(last_sign_in.replace("Z", "+00:00"))
            if last_dt < cutoff:
                reason = f"Licensed but inactive {(datetime.now(timezone.utc) - last_dt).days}d"
        elif has_license and not last_sign_in:
            created = user.get("createdDateTime", "")
            if created:
                created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                if created_dt < cutoff:
                    reason = "Licensed but never signed in"

        if reason:
            orphaned.append({**user, "_orphan_reason": reason})
    return orphaned
