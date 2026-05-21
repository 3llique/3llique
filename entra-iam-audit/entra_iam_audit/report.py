from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from typing import Any

from rich.console import Console
from rich.table import Table
from rich import box
from rich.panel import Panel
from rich.text import Text

console = Console()


def _bool_icon(val: Any) -> str:
    if val is True:
        return "[green]Yes[/green]"
    if val is False:
        return "[red]No[/red]"
    return str(val) if val is not None else "[dim]N/A[/dim]"


def _trunc(s: str, n: int = 40) -> str:
    return s[:n - 1] + "…" if len(s) > n else s


def print_header(title: str, subtitle: str = "") -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    content = Text(title, style="bold white")
    if subtitle:
        content.append(f"\n{subtitle}", style="dim")
    content.append(f"\n{ts}", style="dim cyan")
    console.print(Panel(content, border_style="blue", expand=False))


def print_users(users: list[dict]) -> None:
    table = Table(title=f"All Users ({len(users)})", box=box.ROUNDED, border_style="blue")
    table.add_column("Display Name", style="cyan", max_width=30)
    table.add_column("UPN", style="white", max_width=45)
    table.add_column("Enabled", justify="center")
    table.add_column("Type", style="dim")
    table.add_column("Job Title", style="dim", max_width=25)
    table.add_column("Department", style="dim", max_width=20)
    table.add_column("Last Sign-In", style="yellow", max_width=20)

    for u in users:
        activity = u.get("signInActivity") or {}
        last = activity.get("lastSignInDateTime", "Never")
        if last and last != "Never":
            last = last[:10]

        table.add_row(
            _trunc(u.get("displayName", ""), 30),
            _trunc(u.get("userPrincipalName", ""), 45),
            _bool_icon(u.get("accountEnabled")),
            u.get("userType", "Member"),
            _trunc(u.get("jobTitle") or "", 25),
            _trunc(u.get("department") or "", 20),
            last,
        )
    console.print(table)


def print_stale(stale: list[dict], stale_days: int) -> None:
    table = Table(
        title=f"Stale Accounts — inactive >{stale_days}d ({len(stale)})",
        box=box.ROUNDED, border_style="yellow"
    )
    table.add_column("Display Name", style="cyan", max_width=30)
    table.add_column("UPN", style="white", max_width=45)
    table.add_column("Enabled", justify="center")
    table.add_column("Days Inactive", justify="right", style="red")
    table.add_column("Last Sign-In", style="yellow")

    for u in stale:
        activity = u.get("signInActivity") or {}
        last = activity.get("lastSignInDateTime", "Never")
        if last and last != "Never":
            last = last[:10]
        days = str(u.get("_days_inactive")) if u.get("_days_inactive") else "Never signed in"

        table.add_row(
            _trunc(u.get("displayName", ""), 30),
            _trunc(u.get("userPrincipalName", ""), 45),
            _bool_icon(u.get("accountEnabled")),
            days,
            last,
        )
    console.print(table)


def print_mfa(mfa_statuses: list[dict]) -> None:
    no_mfa = [u for u in mfa_statuses if not u["mfaRegistered"] and u["accountEnabled"]]
    has_mfa = [u for u in mfa_statuses if u["mfaRegistered"]]

    table = Table(
        title=f"MFA Status — {len(has_mfa)}/{len(mfa_statuses)} registered | {len(no_mfa)} enabled users without MFA",
        box=box.ROUNDED, border_style="magenta"
    )
    table.add_column("Display Name", style="cyan", max_width=30)
    table.add_column("UPN", style="white", max_width=45)
    table.add_column("Enabled", justify="center")
    table.add_column("MFA Registered", justify="center")
    table.add_column("Methods", style="green", max_width=35)

    for u in sorted(mfa_statuses, key=lambda x: (x["mfaRegistered"], x["displayName"])):
        table.add_row(
            _trunc(u.get("displayName", ""), 30),
            _trunc(u.get("userPrincipalName", ""), 45),
            _bool_icon(u.get("accountEnabled")),
            _bool_icon(u.get("mfaRegistered")),
            u.get("mfaMethods", ""),
        )
    console.print(table)


def print_roles(role_members: list[dict]) -> None:
    high_priv = [r for r in role_members if r["highPrivilege"]]
    table = Table(
        title=f"Privileged Role Assignments ({len(role_members)} total | {len(high_priv)} high-privilege)",
        box=box.ROUNDED, border_style="red"
    )
    table.add_column("Role", style="red bold", max_width=35)
    table.add_column("High Privilege", justify="center")
    table.add_column("Member", style="cyan", max_width=30)
    table.add_column("UPN / App ID", style="white", max_width=40)
    table.add_column("Type", style="dim")

    for r in sorted(role_members, key=lambda x: (not x["highPrivilege"], x["roleName"])):
        table.add_row(
            r["roleName"],
            "[red]Yes[/red]" if r["highPrivilege"] else "[dim]No[/dim]",
            _trunc(r["memberName"], 30),
            _trunc(r["memberUPN"], 40),
            r["memberType"],
        )
    console.print(table)


def print_licenses(assignments: list[dict], sku_summary: list[dict]) -> None:
    sku_table = Table(title="Tenant License Summary", box=box.ROUNDED, border_style="green")
    sku_table.add_column("License", style="cyan", max_width=45)
    sku_table.add_column("Assigned", justify="right", style="yellow")
    sku_table.add_column("Total", justify="right")
    sku_table.add_column("Available", justify="right", style="green")

    for sku in sorted(sku_summary, key=lambda x: -x["assigned"]):
        avail = sku["available"]
        avail_str = f"[red]{avail}[/red]" if avail < 0 else f"[green]{avail}[/green]"
        sku_table.add_row(
            _trunc(sku["skuName"], 45),
            str(sku["assigned"]),
            str(sku["enabled"]),
            avail_str,
        )
    console.print(sku_table)

    user_table = Table(
        title=f"User License Assignments ({len(assignments)} users)",
        box=box.ROUNDED, border_style="green"
    )
    user_table.add_column("Display Name", style="cyan", max_width=30)
    user_table.add_column("UPN", style="white", max_width=45)
    user_table.add_column("Enabled", justify="center")
    user_table.add_column("#", justify="right")
    user_table.add_column("Licenses", style="green", max_width=50)

    for u in sorted(assignments, key=lambda x: -x["licenseCount"]):
        user_table.add_row(
            _trunc(u.get("displayName", ""), 30),
            _trunc(u.get("userPrincipalName", ""), 45),
            _bool_icon(u.get("accountEnabled")),
            str(u["licenseCount"]),
            _trunc(u["licenses"], 50),
        )
    console.print(user_table)


def print_orphaned(orphaned: list[dict]) -> None:
    table = Table(
        title=f"Orphaned Users ({len(orphaned)})",
        box=box.ROUNDED, border_style="red"
    )
    table.add_column("Display Name", style="cyan", max_width=30)
    table.add_column("UPN", style="white", max_width=45)
    table.add_column("Enabled", justify="center")
    table.add_column("Reason", style="red", max_width=40)

    for u in orphaned:
        table.add_row(
            _trunc(u.get("displayName", ""), 30),
            _trunc(u.get("userPrincipalName", ""), 45),
            _bool_icon(u.get("accountEnabled")),
            u.get("_orphan_reason", ""),
        )
    console.print(table)


def export_csv(data: list[dict], filename: str) -> None:
    clean = [{k: v for k, v in row.items() if not k.startswith("_")} for row in data]
    if not clean:
        return
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(clean[0].keys()))
        writer.writeheader()
        writer.writerows(clean)
    console.print(f"[dim]Exported {len(clean)} rows → {filename}[/dim]")
