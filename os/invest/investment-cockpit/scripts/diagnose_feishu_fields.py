"""Diagnose Feishu Bitable field-name mismatches against BITABLE_SCHEMA."""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict, List

from src.config.settings import load_app_settings
from src.integrations.feishu_bitable import BITABLE_SCHEMA, FeishuBitable
from src.integrations.feishu_client import FeishuApiError, FeishuClient


def list_all_fields(client: FeishuClient, app_token: str, table_id: str) -> List[Dict[str, Any]]:
    path = f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields"
    page_token = ""
    all_items: List[Dict[str, Any]] = []
    while True:
        params: Dict[str, Any] = {"page_size": 500}
        if page_token:
            params["page_token"] = page_token
        data = client.request("GET", path, params=params)
        items = data.get("items", []) or []
        all_items.extend(items)
        if not data.get("has_more"):
            break
        page_token = data.get("page_token", "")
        if not page_token:
            break
    return all_items


def build_expected_by_display_name() -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for spec in BITABLE_SCHEMA.values():
        out[spec["name"]] = [f["field_name"] for f in spec["fields"]]
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose Feishu Bitable field mismatches.")
    parser.add_argument("--app-token", default="", help="Feishu Bitable app token. Defaults to FEISHU_BITABLE_APP_TOKEN.")
    args = parser.parse_args()

    settings = load_app_settings()
    app_token = (args.app_token or settings.feishu_bitable_app_token or "").strip()
    if not app_token:
        print("ERROR: app token is empty. Pass --app-token or set FEISHU_BITABLE_APP_TOKEN.")
        return 2
    if not settings.feishu_app_id or not settings.feishu_app_secret:
        print("ERROR: FEISHU_APP_ID / FEISHU_APP_SECRET missing.")
        return 2

    client = FeishuClient(settings.feishu_app_id, settings.feishu_app_secret)
    bitable = FeishuBitable(client, app_token)
    expected = build_expected_by_display_name()

    try:
        tables = bitable.list_tables()
    except FeishuApiError as exc:
        print(json.dumps({"ok": False, "error": str(exc), "code": exc.code, "msg": exc.feishu_msg}, ensure_ascii=False, indent=2))
        return 1

    report: Dict[str, Any] = {
        "ok": True,
        "app_token": app_token,
        "tables": [],
        "schema_expected_tables": list(expected.keys()),
        "missing_tables": [],
        "extra_tables": [],
    }

    actual_table_names = [t.get("name", "") for t in tables]
    report["missing_tables"] = [name for name in expected.keys() if name not in actual_table_names]
    report["extra_tables"] = [name for name in actual_table_names if name not in expected.keys()]

    for table in tables:
        table_name = table.get("name", "")
        table_id = table.get("table_id", "")
        fields = list_all_fields(client, app_token, table_id)
        actual_field_names = [f.get("field_name", "") for f in fields]

        expected_field_names = expected.get(table_name, [])
        missing_fields = [f for f in expected_field_names if f not in actual_field_names]
        extra_fields = [f for f in actual_field_names if f not in expected_field_names] if expected_field_names else list(actual_field_names)

        report["tables"].append(
            {
                "table_name": table_name,
                "table_id": table_id,
                "actual_fields": actual_field_names,
                "expected_fields": expected_field_names,
                "missing_fields": missing_fields,
                "extra_fields": extra_fields,
                "matches_schema": (len(missing_fields) == 0 and len(extra_fields) == 0 and bool(expected_field_names)),
            }
        )

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
