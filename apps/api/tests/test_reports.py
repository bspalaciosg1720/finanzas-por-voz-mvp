from io import BytesIO

from app.modules.reports.service import period_bounds
from fastapi.testclient import TestClient
from openpyxl import load_workbook
from tests.test_transactions import auth_headers, create, payload, register


def test_monthly_report_aggregates_totals_and_categories(client: TestClient) -> None:
    auth = register(client, "reports@example.com")
    create(
        client,
        auth,
        payload(
            amount=1_000_000,
            movement_type="income",
            occurred_at="2026-07-01T12:00:00-05:00",
        ),
    )
    create(
        client,
        auth,
        payload(amount=250_000, occurred_at="2026-07-31T12:00:00-05:00"),
    )
    create(
        client,
        auth,
        payload(amount=99_000, occurred_at="2026-08-02T12:00:00-05:00"),
    )

    response = client.get(
        "/api/v1/reports/summary?period=monthly&anchor=2026-07-15",
        headers=auth_headers(auth),
    )
    assert response.status_code == 200
    report = response.json()
    assert report["start_date"] == "2026-07-01"
    assert report["end_date"] == "2026-07-31"
    assert report["income_minor"] == 1_000_000
    assert report["expense_minor"] == 250_000
    assert report["balance_minor"] == 750_000
    assert report["transaction_count"] == 2
    assert report["categories"][0]["percentage"] == 100.0
    assert len(report["series"]) == 2


def test_report_periods_and_user_isolation(client: TestClient) -> None:
    owner = register(client, "report-owner@example.com")
    other = register(client, "report-other@example.com")
    create(
        client,
        owner,
        payload(amount=10_000, occurred_at="2026-07-29T12:00:00-05:00"),
    )
    create(
        client,
        other,
        payload(amount=90_000, occurred_at="2026-07-29T12:00:00-05:00"),
    )

    weekly = client.get(
        "/api/v1/reports/summary?period=weekly&anchor=2026-07-30",
        headers=auth_headers(owner),
    ).json()
    assert weekly["start_date"] == "2026-07-27"
    assert weekly["end_date"] == "2026-08-02"
    assert weekly["expense_minor"] == 10_000

    annual = client.get(
        "/api/v1/reports/summary?period=annual&anchor=2026-07-30",
        headers=auth_headers(owner),
    ).json()
    assert annual["start_date"] == "2026-01-01"
    assert annual["end_date"] == "2026-12-31"


def test_report_compares_with_previous_period(client: TestClient) -> None:
    auth = register(client, "report-comparison@example.com")
    create(
        client,
        auth,
        payload(amount=100_000, occurred_at="2026-06-15T12:00:00-05:00"),
    )
    create(
        client,
        auth,
        payload(amount=150_000, occurred_at="2026-07-15T12:00:00-05:00"),
    )
    report = client.get(
        "/api/v1/reports/summary?period=monthly&anchor=2026-07-15",
        headers=auth_headers(auth),
    ).json()
    assert report["previous_expense_minor"] == 100_000
    assert report["expense_change_percent"] == 50.0


def test_period_bounds_are_calendar_aligned() -> None:
    from datetime import date

    assert period_bounds(date(2026, 7, 30), "daily") == (
        date(2026, 7, 30),
        date(2026, 7, 30),
    )
    assert period_bounds(date(2026, 7, 30), "monthly") == (
        date(2026, 7, 1),
        date(2026, 7, 31),
    )


def test_csv_export_uses_period_and_excludes_other_users(client: TestClient) -> None:
    owner = register(client, "csv-owner@example.com")
    other = register(client, "csv-other@example.com")
    create(
        client,
        owner,
        payload(
            amount=28_500,
            description="Transporte, centro",
            occurred_at="2026-07-15T12:00:00-05:00",
        ),
    )
    create(
        client,
        other,
        payload(
            amount=999_000,
            description="No debe aparecer",
            occurred_at="2026-07-15T12:00:00-05:00",
        ),
    )
    response = client.get(
        "/api/v1/reports/exports/csv?period=monthly&anchor=2026-07-15",
        headers=auth_headers(owner),
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "movimientos-monthly-2026-07-01-2026-07-31.csv" in response.headers[
        "content-disposition"
    ]
    assert response.content.startswith(b"\xef\xbb\xbf")
    text = response.content.decode("utf-8-sig")
    assert "Transporte, centro" in text
    assert "No debe aparecer" not in text


def test_xlsx_and_pdf_exports_are_valid_documents(client: TestClient) -> None:
    auth = register(client, "document-exports@example.com")
    create(
        client,
        auth,
        payload(
            amount=45_000,
            description="Educación & libros",
            occurred_at="2026-07-15T12:00:00-05:00",
        ),
    )
    query = "?period=monthly&anchor=2026-07-15"
    xlsx = client.get(
        f"/api/v1/reports/exports/xlsx{query}", headers=auth_headers(auth)
    )
    assert xlsx.status_code == 200
    workbook = load_workbook(BytesIO(xlsx.content), read_only=True)
    values = list(workbook["Movimientos"].values)
    assert values[0][0] == "Fecha"
    assert values[1][5] == "Educación & libros"

    pdf = client.get(
        f"/api/v1/reports/exports/pdf{query}", headers=auth_headers(auth)
    )
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content.startswith(b"%PDF-")
    assert len(pdf.content) > 1_000
