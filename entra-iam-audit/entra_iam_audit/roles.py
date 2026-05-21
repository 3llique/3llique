from __future__ import annotations

from .graph_client import GraphClient

# Well-known high-privilege role template IDs
HIGH_PRIVILEGE_ROLES = {
    "62e90394-69f5-4237-9190-012177145e10": "Global Administrator",
    "e8611ab8-c189-46e8-94e1-60213ab1f814": "Privileged Role Administrator",
    "194ae4cb-b126-40b2-bd5b-6091b380977d": "Security Administrator",
    "9b895d92-2cd3-44c7-9d02-a6ac2d5ea5c3": "Application Administrator",
    "c4e39bd9-1100-46d3-8c65-fb160da0071f": "Authentication Administrator",
    "b0f54661-2d74-4c50-afa3-1ec803f12efe": "Billing Administrator",
    "29232cdf-9323-42fd-ade2-1d097af3e4de": "Exchange Administrator",
    "f28a1f50-f6e7-4571-818b-6a12f2af6b6c": "SharePoint Administrator",
    "fe930be7-5e62-47db-91af-98c3a49a38b1": "User Administrator",
    "729827e3-9c14-49f7-bb1b-9608f156bbb8": "Helpdesk Administrator",
    "966707d0-3269-4727-9be2-8c3a10f19b9d": "Password Administrator",
    "7be44c8a-adaf-4e2a-84d6-ab2649e08a13": "Privileged Authentication Administrator",
}


def fetch_privileged_role_members(client: GraphClient) -> list[dict]:
    """Return all members of privileged directory roles."""
    roles = client.get_all("/directoryRoles")
    findings: list[dict] = []

    for role in roles:
        role_id = role.get("id", "")
        role_name = role.get("displayName", "Unknown Role")
        template_id = role.get("roleTemplateId", "")
        is_high_privilege = template_id in HIGH_PRIVILEGE_ROLES

        members = client.get_all(f"/directoryRoles/{role_id}/members")
        for member in members:
            findings.append({
                "roleId": role_id,
                "roleName": role_name,
                "highPrivilege": is_high_privilege,
                "memberId": member.get("id", ""),
                "memberName": member.get("displayName", ""),
                "memberUPN": member.get("userPrincipalName", member.get("appId", "")),
                "memberType": member.get("@odata.type", "").split(".")[-1],
            })

    return findings


def get_high_privilege_summary(role_members: list[dict]) -> list[dict]:
    return [r for r in role_members if r["highPrivilege"]]
