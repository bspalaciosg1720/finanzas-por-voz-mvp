from datetime import date, datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.modules.auth.dependencies import CurrentUser
from app.modules.reports.schemas import ReportPeriod, ReportSummary
from app.modules.reports.service import export_csv, export_pdf, export_xlsx, get_report

router = APIRouter(prefix="/reports", tags=["Reports"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("/summary", response_model=ReportSummary)
def report_summary(
    user: CurrentUser,
    db: DbSession,
    period: Annotated[ReportPeriod, Query()] = "monthly",
    anchor: Annotated[date | None, Query()] = None,
) -> ReportSummary:
    selected = anchor or datetime.now(ZoneInfo(user.timezone)).date()
    return get_report(db, user, period=period, anchor=selected)


@router.get("/exports/csv")
def report_csv(
    user: CurrentUser,
    db: DbSession,
    period: Annotated[ReportPeriod, Query()] = "monthly",
    anchor: Annotated[date | None, Query()] = None,
) -> Response:
    selected = anchor or datetime.now(ZoneInfo(user.timezone)).date()
    filename, content = export_csv(db, user, period=period, anchor=selected)
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _download(filename: str, content: bytes, media_type: str) -> Response:
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/exports/xlsx")
def report_xlsx(
    user: CurrentUser,
    db: DbSession,
    period: Annotated[ReportPeriod, Query()] = "monthly",
    anchor: Annotated[date | None, Query()] = None,
) -> Response:
    selected = anchor or datetime.now(ZoneInfo(user.timezone)).date()
    filename, content = export_xlsx(db, user, period=period, anchor=selected)
    return _download(
        filename,
        content,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.get("/exports/pdf")
def report_pdf(
    user: CurrentUser,
    db: DbSession,
    period: Annotated[ReportPeriod, Query()] = "monthly",
    anchor: Annotated[date | None, Query()] = None,
) -> Response:
    selected = anchor or datetime.now(ZoneInfo(user.timezone)).date()
    filename, content = export_pdf(db, user, period=period, anchor=selected)
    return _download(filename, content, "application/pdf")
