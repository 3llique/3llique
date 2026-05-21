from __future__ import annotations

from .graph_client import GraphClient

# Authentication method types that satisfy MFA
MFA_METHOD_TYPES = {
    "#microsoft.graph.microsoftAuthenticatorAuthenticationMethod",
    "#microsoft.graph.phoneAuthenticationMethod",
    "#microsoft.graph.fido2AuthenticationMethod",
    "#microsoft.graph.softwareOathAuthenticationMethod",
    "#microsoft.graph.temporaryAccessPassAuthenticationMethod",
    "#microsoft.graph.windowsHelloForBusinessAuthenticationMethod",
    "#microsoft.graph.emailAuthenticationMethod",
}


def fetch_user_mfa_status(client: GraphClient, user_id: str) -> dict:
    try:
        methods = client.get_all(f"/users/{user_id}/authentication/methods")
    except Exception:
        return {"registered": False, "methods": [], "error": True}

    registered_types = [m.get("@odata.type", "") for m in methods]
    mfa_methods = [t for t in registered_types if t in MFA_METHOD_TYPES]
    return {
        "registered": bool(mfa_methods),
        "methods": [_friendly_method_name(t) for t in mfa_methods],
        "error": False,
    }


def fetch_all_mfa_statuses(client: GraphClient, users: list[dict]) -> list[dict]:
    results = []
    for user in users:
        status = fetch_user_mfa_status(client, user["id"])
        results.append({
            "id": user["id"],
            "displayName": user.get("displayName", ""),
            "userPrincipalName": user.get("userPrincipalName", ""),
            "accountEnabled": user.get("accountEnabled", True),
            "mfaRegistered": status["registered"],
            "mfaMethods": ", ".join(status["methods"]) if status["methods"] else "None",
        })
    return results


def _friendly_method_name(odata_type: str) -> str:
    mapping = {
        "#microsoft.graph.microsoftAuthenticatorAuthenticationMethod": "Authenticator App",
        "#microsoft.graph.phoneAuthenticationMethod": "Phone (SMS/Call)",
        "#microsoft.graph.fido2AuthenticationMethod": "FIDO2 Security Key",
        "#microsoft.graph.softwareOathAuthenticationMethod": "OATH TOTP",
        "#microsoft.graph.temporaryAccessPassAuthenticationMethod": "Temporary Access Pass",
        "#microsoft.graph.windowsHelloForBusinessAuthenticationMethod": "Windows Hello",
        "#microsoft.graph.emailAuthenticationMethod": "Email OTP",
    }
    return mapping.get(odata_type, odata_type.split(".")[-1])
