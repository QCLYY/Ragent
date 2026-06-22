# backend/research/routes.py
"""Research API endpoints.

POST   /research/create         — Create and start a research task
GET    /research/list           — List user's research executions
GET    /research/{id}           — Get research status + progress
GET    /research/{id}/evidence  — List collected evidence
GET    /research/{id}/report    — Get generated report
POST   /research/{id}/cancel    — Cancel running research
"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from backend.auth.dependencies import UserContext, get_current_user
from backend.research.planner import get_research_planner
from backend.research.executor import get_research_executor
from backend.research.evidence_store import get_evidence_store
from backend.research.models import ResearchExecution, ResearchReportRecord
from backend.storage.database import SessionLocal

router = APIRouter(prefix="/research", tags=["research"])


# NOTE: /list must come BEFORE /{execution_id} to prevent FastAPI from
# matching "list" as an execution_id parameter.


@router.post("/create")
async def create_research(
    request: dict,
    background_tasks: BackgroundTasks,
    user: UserContext = Depends(get_current_user),
):
    """Create and start a new research task."""
    goal = request.get("goal", "").strip()
    if not goal:
        raise HTTPException(status_code=400, detail="goal is required")

    import uuid
    execution_id = f"rx_{uuid.uuid4().hex[:16]}"

    # 1. Plan
    planner = get_research_planner()
    plan = await planner.plan(goal)

    # 2. Create execution record immediately so frontend can poll
    db = SessionLocal()
    try:
        record = ResearchExecution(
            execution_id=execution_id,
            tenant_id=user.tenant_id,
            user_id=user.user_id,
            session_id=request.get("session_id", ""),
            goal=plan.goal,
            plan_json=plan.model_dump(),
            status="running",
        )
        db.add(record)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create research execution")
    finally:
        db.close()

    # 3. Execute in background via asyncio.create_task (more reliable than BackgroundTasks)
    import asyncio
    executor = get_research_executor()

    async def run_research():
        try:
            await executor.execute(
                execution_id=execution_id,
                plan=plan,
                tenant_id=user.tenant_id,
                user_id=user.user_id,
                session_id=request.get("session_id", ""),
            )
        except Exception:
            pass  # Errors are already handled inside executor.execute()

    asyncio.create_task(run_research())

    return {
        "execution_id": execution_id,
        "plan": plan.model_dump(),
        "status": "started",
        "message": f"Research started with {len(plan.tasks)} tasks, estimated {plan.estimated_duration_minutes} min",
    }


@router.get("/list")
async def list_research(
    user: UserContext = Depends(get_current_user),
):
    """List user's research executions."""
    db = SessionLocal()
    try:
        records = (
            db.query(ResearchExecution)
            .filter(ResearchExecution.tenant_id == user.tenant_id)
            .order_by(ResearchExecution.created_at.desc())
            .limit(50)
            .all()
        )
        return {
            "executions": [
                {
                    "execution_id": r.execution_id,
                    "goal": r.goal,
                    "status": r.status,
                    "progress": r.progress,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in records
            ]
        }
    finally:
        db.close()


@router.get("/{execution_id}")
async def get_research_status(
    execution_id: str,
    user: UserContext = Depends(get_current_user),
):
    """Get research execution status and progress."""
    db = SessionLocal()
    try:
        record = (
            db.query(ResearchExecution)
            .filter(
                ResearchExecution.execution_id == execution_id,
                ResearchExecution.tenant_id == user.tenant_id,
            )
            .first()
        )
        if not record:
            raise HTTPException(status_code=404, detail="Research not found")

        return {
            "execution_id": record.execution_id,
            "goal": record.goal,
            "status": record.status,
            "progress": record.progress,
            "review_count": record.review_count,
            "error_message": record.error_message,
            "started_at": record.started_at.isoformat() if record.started_at else None,
            "completed_at": record.completed_at.isoformat() if record.completed_at else None,
        }
    finally:
        db.close()


@router.get("/{execution_id}/evidence")
async def get_research_evidence(
    execution_id: str,
    user: UserContext = Depends(get_current_user),
):
    """List all evidence collected for a research execution."""
    db = SessionLocal()
    try:
        record = (
            db.query(ResearchExecution)
            .filter(
                ResearchExecution.execution_id == execution_id,
                ResearchExecution.tenant_id == user.tenant_id,
            )
            .first()
        )
        if not record:
            raise HTTPException(status_code=404, detail="Research not found")

        store = get_evidence_store()
        evidence = store.get_by_execution(record.id)
        stats = store.get_stats(record.id)

        return {
            "execution_id": execution_id,
            "stats": stats,
            "evidence": [e.model_dump() for e in evidence],
        }
    finally:
        db.close()


@router.get("/{execution_id}/report")
async def get_research_report(
    execution_id: str,
    format: str = "markdown",
    user: UserContext = Depends(get_current_user),
):
    """Get generated research report."""
    db = SessionLocal()
    try:
        record = (
            db.query(ResearchExecution)
            .filter(
                ResearchExecution.execution_id == execution_id,
                ResearchExecution.tenant_id == user.tenant_id,
            )
            .first()
        )
        if not record:
            raise HTTPException(status_code=404, detail="Research not found")

        report = (
            db.query(ResearchReportRecord)
            .filter(
                ResearchReportRecord.execution_id == record.id,
                ResearchReportRecord.format == format,
            )
            .order_by(ResearchReportRecord.created_at.desc())
            .first()
        )
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        content = report.content or ""
        original_content = content
        evidence_map = report.evidence_map_json or {}
        original_evidence_map = evidence_map
        try:
            from backend.research.report_generator import get_report_generator

            generator = get_report_generator()
            needs_rebuild = (
                not evidence_map
                or any(
                    not generator._is_valid_citation(str(ref))
                    for ref in evidence_map.values()
                )
                or "## 参考文献" not in content
            )
            if needs_rebuild:
                evidence_items = get_evidence_store().get_by_execution(record.id)
                rebuilt_map = {}
                for idx, ev in enumerate(evidence_items, 1):
                    rebuilt_map[f"[证据{idx}]"] = generator._format_reference(ev)
                evidence_map = rebuilt_map or evidence_map
            content = generator._replace_references_section(content, evidence_map)
            if content != original_content or evidence_map != original_evidence_map:
                report.content = content
                report.evidence_map_json = evidence_map
                db.commit()
        except Exception:
            pass

        return {
            "report_id": report.report_id,
            "title": report.title,
            "format": report.format,
            "content": content,
            "summary": report.summary,
            "evidence_map": evidence_map,
        }
    finally:
        db.close()


@router.post("/{execution_id}/cancel")
async def cancel_research(
    execution_id: str,
    user: UserContext = Depends(get_current_user),
):
    """Cancel a running research execution."""
    db = SessionLocal()
    try:
        record = (
            db.query(ResearchExecution)
            .filter(
                ResearchExecution.execution_id == execution_id,
                ResearchExecution.tenant_id == user.tenant_id,
            )
            .first()
        )
        if not record:
            raise HTTPException(status_code=404, detail="Research not found")
        if record.status not in ("pending", "running"):
            raise HTTPException(status_code=400, detail="Research already finished")

        record.status = "cancelled"
        db.commit()
        return {"status": "cancelled", "execution_id": execution_id}
    finally:
        db.close()


@router.delete("/{execution_id}")
async def delete_research(
    execution_id: str,
    user: UserContext = Depends(get_current_user),
):
    """Delete a research execution and its evidence/reports."""
    db = SessionLocal()
    try:
        record = (
            db.query(ResearchExecution)
            .filter(
                ResearchExecution.execution_id == execution_id,
                ResearchExecution.tenant_id == user.tenant_id,
            )
            .first()
        )
        if not record:
            raise HTTPException(status_code=404, detail="Research not found")
        # ORM cascade handles children via relationship cascade='all, delete-orphan'
        db.delete(record)
        db.commit()
        return {"status": "deleted", "execution_id": execution_id}
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete research")
    finally:
        db.close()
