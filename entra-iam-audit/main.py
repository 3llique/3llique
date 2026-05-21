#!/usr/bin/env python3
"""Entra IAM Audit Tool — audit Microsoft Entra ID (Azure AD) via Graph API."""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console

from entra_iam_audit.auth import GraphAuth
from entra_iam_audit.graph_client import GraphClient
from entra_iam_audit import report
from entra_iam_audit.users import fetch_all_users, get_stale_accounts, get_orphaned_users
from entra_iam_audit.mfa import fetch_all_mfa_statuses
from entra_iam_audit.roles import fetch_privileged_role_members
from entra_iam_audit.licenses import fetch_license_assignments, fetch_sku_summary

console = Console()

COMMANDS = ["all", "users", "stale", "mfa", "roles", "licenses", "orphaned"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="entra-audit",
        description="Microsoft Entra ID IAM Audit Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  all        Run every audit module
  users      List all users with sign-in activity
  stale      Find accounts inactive longer than --stale-days
  mfa        Show MFA registration status per user
  roles      List privileged directory role assignments
  licenses   Show tenant license summary and user assignments
  orphaned   Find disabled-but-licensed or long-inactive licensed users

Examples:
  python main.py all
  python main.py stale --stale-days 60 --export stale.csv
  python main.py mfa --export mfa_report.csv
  python main.py roles
        """,
    )
    parser.add_argument("command", choices=COMMANDS, help="Audit module to run")
    parser.add_argument(
        "--stale-days",
        type=int,
        default=int(os.getenv("STALE_DAYS", "90")),
        help="Days of inactivity to flag as stale (default: 90)",
    )
    parser.add_argument(
        "--export",
        metavar="FILE.csv",
        help="Export results to CSV file",
    )
    parser.add_argument(
        "--env",
        default=".env",
        help="Path to .env file (default: .env)",
    )
    return parser


def load_credentials(env_file: str) -> tuple[str, str, str | None]:
    load_dotenv(env_file)
    tenant_id = os.getenv("TENANT_ID")
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    if not tenant_id or not client_id:
        console.print(
            "[red]Error:[/red] TENANT_ID and CLIENT_ID must be set in .env or environment.\n"
            f"Copy .env.example to .env and fill in your credentials."
        )
        sys.exit(1)
    return tenant_id, client_id, client_secret


def run_users(client: GraphClient, args: argparse.Namespace) -> list[dict]:
    console.print("[dim]Fetching users…[/dim]")
    users = fetch_all_users(client)
    report.print_users(users)
    if args.export:
        report.export_csv(users, args.export)
    return users


def run_stale(client: GraphClient, args: argparse.Namespace, users: list[dict] | None = None) -> list[dict]:
    if users is None:
        console.print("[dim]Fetching users…[/dim]")
        users = fetch_all_users(client)
    stale = get_stale_accounts(users, args.stale_days)
    report.print_stale(stale, args.stale_days)
    if args.export:
        report.export_csv(stale, args.export)
    return stale


def run_mfa(client: GraphClient, args: argparse.Namespace, users: list[dict] | None = None) -> list[dict]:
    if users is None:
        console.print("[dim]Fetching users…[/dim]")
        users = fetch_all_users(client)
    console.print(f"[dim]Checking MFA for {len(users)} users (this may take a moment)…[/dim]")
    statuses = fetch_all_mfa_statuses(client, users)
    report.print_mfa(statuses)
    if args.export:
        report.export_csv(statuses, args.export)
    return statuses


def run_roles(client: GraphClient, args: argparse.Namespace) -> list[dict]:
    console.print("[dim]Fetching privileged role assignments…[/dim]")
    members = fetch_privileged_role_members(client)
    report.print_roles(members)
    if args.export:
        report.export_csv(members, args.export)
    return members


def run_licenses(client: GraphClient, args: argparse.Namespace, users: list[dict] | None = None) -> list[dict]:
    if users is None:
        console.print("[dim]Fetching users…[/dim]")
        users = fetch_all_users(client)
    console.print("[dim]Fetching SKU summary…[/dim]")
    sku_summary = fetch_sku_summary(client)
    assignments = fetch_license_assignments(users)
    report.print_licenses(assignments, sku_summary)
    if args.export:
        report.export_csv(assignments, args.export)
    return assignments


def run_orphaned(client: GraphClient, args: argparse.Namespace, users: list[dict] | None = None) -> list[dict]:
    if users is None:
        console.print("[dim]Fetching users…[/dim]")
        users = fetch_all_users(client)
    orphaned = get_orphaned_users(users)
    report.print_orphaned(orphaned)
    if args.export:
        report.export_csv(orphaned, args.export)
    return orphaned


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    tenant_id, client_id, client_secret = load_credentials(args.env)
    auth = GraphAuth(tenant_id, client_id, client_secret)
    client = GraphClient(auth)

    report.print_header(
        "Entra IAM Audit Tool",
        f"Tenant: {tenant_id}  |  Module: {args.command}",
    )

    try:
        if args.command == "all":
            users = fetch_all_users(client)
            console.print(f"[dim]Loaded {len(users)} users.[/dim]\n")
            report.print_users(users)
            run_stale(client, args, users)
            run_mfa(client, args, users)
            run_roles(client, args)
            run_licenses(client, args, users)
            run_orphaned(client, args, users)
        elif args.command == "users":
            run_users(client, args)
        elif args.command == "stale":
            run_stale(client, args)
        elif args.command == "mfa":
            run_mfa(client, args)
        elif args.command == "roles":
            run_roles(client, args)
        elif args.command == "licenses":
            run_licenses(client, args)
        elif args.command == "orphaned":
            run_orphaned(client, args)
    except KeyboardInterrupt:
        console.print("\n[yellow]Audit interrupted.[/yellow]")
        sys.exit(0)
    except Exception as exc:
        console.print(f"[red]Error:[/red] {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
