from __future__ import annotations

from .graph_client import GraphClient

# Common Microsoft SKU friendly names (partial list of most common)
SKU_NAMES: dict[str, str] = {
    "6fd2c87f-b296-42f0-b197-1e91e994b900": "Microsoft 365 E3",
    "c7df2760-2c81-4ef7-b578-5b5392b571df": "Microsoft 365 E5",
    "b05e124f-c7cc-45a0-a6aa-8cf78c946968": "Enterprise Mobility + Security E5",
    "efccb6f7-5641-4e0e-bd10-b4976e1bf68e": "Enterprise Mobility + Security E3",
    "f30db892-07e9-47e9-837c-80727f46fd3d": "Microsoft Flow Free",
    "18181a46-0d4e-45cd-891e-60aabd171b4e": "Office 365 E1",
    "6634e0ce-1a9f-428c-a498-f84ec7b8aa2e": "Office 365 E2",
    "6fd2c87f-b296-42f0-b197-1e91e994b900": "Office 365 E3",
    "1392051d-0cb9-4b7a-88d5-621fee5e8711": "Office 365 E4",
    "c7df2760-2c81-4ef7-b578-5b5392b571df": "Office 365 E5",
    "4b585984-651b-448a-9e53-3b10f069cf7f": "Office 365 F3",
    "710779e8-3d4a-4c88-adb9-386c958d1fdf": "Microsoft Teams Essentials",
    "0c266dff-15dd-4b49-8397-2bb16070ed52": "Microsoft Teams Exploratory",
    "3ab6abff-666f-4424-bfb7-f0bc274ec7bc": "Power BI Pro",
    "f8a1db68-be16-40ed-86d5-cb42ce701560": "Power BI Premium Per User",
    "b3b86b9f-6ce6-4924-95b4-aec30b80b517": "Visio Plan 1",
    "4b244418-9658-4451-a2b8-b5e2b364e9bd": "Visio Plan 2",
    "a403ebcc-fae0-4ca2-8c8c-7a907fd6c235": "Power Apps Per User Plan",
    "d9f8c498-b2db-4cbb-bca5-84e7a1ec42c3": "Dynamics 365 Sales Professional",
    "e43b5b99-8dfb-405f-9987-dc307f34bcbd": "Microsoft Defender for Endpoint P2",
    "06ebc4ee-1bb5-47dd-8120-11324bc54e06": "Microsoft 365 Business Premium",
    "cbdc14ab-d96c-4c30-b9f4-6ada7cdc1d46": "Microsoft 365 Business Basic",
    "b214fe43-f571-4113-a89f-6e58b8d2abb4": "Microsoft 365 Business Standard",
    "93f7cccd-fa6b-4db3-8dcc-2e7ce5ca6a7e": "Azure AD Premium P1",
    "84a661c4-e949-4bd2-a560-ed7766fcaf2b": "Azure AD Premium P2",
}


def fetch_license_assignments(users: list[dict]) -> list[dict]:
    assignments = []
    for user in users:
        licenses = user.get("assignedLicenses") or []
        sku_names = [_sku_friendly_name(lic.get("skuId", "")) for lic in licenses]
        assignments.append({
            "id": user["id"],
            "displayName": user.get("displayName", ""),
            "userPrincipalName": user.get("userPrincipalName", ""),
            "accountEnabled": user.get("accountEnabled", True),
            "licenseCount": len(licenses),
            "licenses": ", ".join(sku_names) if sku_names else "None",
        })
    return assignments


def fetch_sku_summary(client: GraphClient) -> list[dict]:
    """Return tenant-wide SKU usage summary."""
    skus = client.get_all("/subscribedSkus")
    summary = []
    for sku in skus:
        prepaid = sku.get("prepaidUnits", {})
        summary.append({
            "skuId": sku.get("skuId", ""),
            "skuName": _sku_friendly_name(sku.get("skuId", "")) or sku.get("skuPartNumber", ""),
            "assigned": sku.get("consumedUnits", 0),
            "enabled": prepaid.get("enabled", 0),
            "suspended": prepaid.get("suspended", 0),
            "warning": prepaid.get("warning", 0),
            "available": prepaid.get("enabled", 0) - sku.get("consumedUnits", 0),
        })
    return summary


def _sku_friendly_name(sku_id: str) -> str:
    return SKU_NAMES.get(sku_id, sku_id)
