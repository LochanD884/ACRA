import asyncio
import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.db import get_db, AsyncSessionLocal
from app.models.analysis import Analysis
from app.schemas.analysis import AnalysisCreate, AnalysisDetail, AnalysisList, AnalysisOut
from app.services.analysis_agent import AnalysisAgent, AnalysisInput
from app.services.progress import progress_hub
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()
agent = AnalysisAgent()


@router.post("/analyze", response_model=AnalysisOut)
async def create_analysis(payload: AnalysisCreate, db: AsyncSession = Depends(get_db)):
    if not settings.openrouter_api_key:
        raise HTTPException(status_code=400, detail="OPENROUTER_API_KEY is not configured")

    analysis = Analysis(
        repo_url=str(payload.repo_url),
        pr_number=payload.pr_number,
        status="queued",
        progress=0,
        extra_metadata={
            "allow_git_clone": payload.allow_git_clone,
            "thread_name": payload.thread_name.strip() if payload.thread_name else None,
        },
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)

    task_payload = AnalysisInput(
        repo_url=str(payload.repo_url),
        pr_number=payload.pr_number,
        github_token=payload.github_token,
        allow_git_clone=payload.allow_git_clone,
    )

    async def runner() -> None:
        async with AsyncSessionLocal() as session:
            await agent.run(analysis.id, session, task_payload)

    asyncio.create_task(runner())
    return analysis


@router.get("/analyses", response_model=AnalysisList)
async def list_analyses(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Analysis).order_by(Analysis.created_at.desc()))
    items = result.scalars().all()
    return AnalysisList(items=items)


@router.get("/analyses/{analysis_id}", response_model=AnalysisDetail)
async def get_analysis(analysis_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Analysis).options(selectinload(Analysis.issues)).where(Analysis.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


@router.delete("/analyses/{analysis_id}")
async def delete_analysis(analysis_id: int, db: AsyncSession = Depends(get_db)):
    analysis = await db.get(Analysis, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    await db.delete(analysis)
    await db.commit()
    return {"status": "deleted"}


@router.get("/analyses/{analysis_id}/events")
async def analysis_events(analysis_id: int):
    queue = progress_hub.get_queue(analysis_id)

    async def event_generator():
        while True:
            update = await queue.get()
            yield {
                "event": "progress",
                "data": json.dumps({
                    "status": update.status,
                    "progress": update.progress,
                    "message": update.message,
                }),
            }
            if update.status in {"completed", "failed"}:
                break

    return EventSourceResponse(event_generator())
