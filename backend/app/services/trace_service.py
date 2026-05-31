"""Trace 服务 — Trace / Span / Generation CRUD"""

from datetime import datetime
from typing import Optional

from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.trace import Generation, Span, Trace
from app.models.score import Score
from app.utils.helpers import gen_uuid


class TraceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================
    # Trace
    # ============================

    async def create_trace(
        self,
        project_id: str,
        name: str,
        user_id: str | None = None,
        session_id: str | None = None,
        tags: list | None = None,
        metadata: dict | None = None,
        release: str | None = None,
        version: str | None = None,
        trace_id: str | None = None,
    ) -> Trace:
        now = datetime.utcnow()
        trace = Trace(
            id=trace_id or gen_uuid(),
            project_id=project_id,
            name=name,
            user_id=user_id,
            session_id=session_id,
            tags=tags,
            extra_metadata=metadata,
            release=release,
            version=version,
            status="in_progress",
            started_at=now,
        )
        self.db.add(trace)
        await self.db.commit()
        await self.db.refresh(trace)
        return trace

    async def get_trace(self, trace_id: str) -> Trace | None:
        result = await self.db.execute(
            select(Trace)
            .options(
                selectinload(Trace.spans).selectinload(Span.generations),
                selectinload(Trace.scores),
            )
            .where(Trace.id == trace_id)
        )
        return result.scalar_one_or_none()

    async def get_traces(
        self,
        *,
        project_id: str | None = None,
        status: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        tags: list[str] | None = None,
        keyword: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        query = select(Trace).order_by(desc(Trace.started_at))

        if project_id:
            query = query.where(Trace.project_id == project_id)
        if status:
            query = query.where(Trace.status == status)
        if start_date:
            query = query.where(Trace.started_at >= start_date)
        if end_date:
            query = query.where(Trace.started_at <= end_date)
        if keyword:
            query = query.where(
                or_(
                    Trace.name.ilike(f"%{keyword}%"),
                    Trace.user_id.ilike(f"%{keyword}%"),
                )
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        items = (
            await self.db.execute(
                query.offset((page - 1) * page_size).limit(page_size)
            )
        ).scalars().all()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items,
        }

    ALLOWED_UPDATE_FIELDS = {
        "name", "user_id", "tags", "extra_metadata", "release", "version",
        "status", "error_message",
    }

    async def update_trace(self, trace_id: str, **kwargs) -> Trace | None:
        trace = await self.get_trace(trace_id)
        if trace is None:
            return None
        for key, value in kwargs.items():
            if key in self.ALLOWED_UPDATE_FIELDS and value is not None:
                setattr(trace, key, value)
        await self.db.commit()
        await self.db.refresh(trace)
        return trace

    async def complete_trace(self, trace_id: str) -> Trace | None:
        trace = await self.get_trace(trace_id)
        if trace is None:
            return None

        now = datetime.utcnow()
        trace.status = "completed"
        trace.completed_at = now

        if trace.started_at:
            trace.total_latency_ms = (now - trace.started_at).total_seconds() * 1000

        from app.evaluators.builtin.token_cost import MODEL_PRICING

        total_tokens = 0
        total_cost = 0.0
        for span in trace.spans:
            for gen in span.generations:
                usage = gen.usage or {}
                total_tokens += usage.get("total_tokens", 0)

                if gen.cost is not None and gen.cost > 0:
                    total_cost += gen.cost
                elif usage:
                    pricing = MODEL_PRICING.get(gen.model, {})
                    prompt_tokens = usage.get("prompt_tokens", 0)
                    completion_tokens = usage.get("completion_tokens", 0)
                    cost = (prompt_tokens / 1_000_000) * pricing.get("input", 0) + \
                           (completion_tokens / 1_000_000) * pricing.get("output", 0)
                    gen.cost = cost
                    total_cost += cost

        trace.total_tokens = total_tokens or None
        trace.total_cost = round(total_cost, 6) if total_cost > 0 else None

        await self.db.commit()
        await self.db.refresh(trace)
        return trace

    async def delete_trace(self, trace_id: str) -> bool:
        trace = await self.get_trace(trace_id)
        if trace is None:
            return False
        await self.db.delete(trace)
        await self.db.commit()
        return True

    # ============================
    # Span
    # ============================

    async def create_span(
        self,
        trace_id: str,
        name: str,
        type: str = "span",
        parent_span_id: str | None = None,
        input: dict | None = None,
        output: dict | None = None,
        metadata: dict | None = None,
        model: str | None = None,
        span_id: str | None = None,
        started_at: datetime | None = None,
        level: int = 0,
    ) -> Span:
        # 如果提供了 output，说明 span 已经执行完毕，自动标记为 completed
        has_output = output is not None and len(output) > 0
        now = datetime.utcnow()
        started = started_at or now
        span = Span(
            id=span_id or gen_uuid(),
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            name=name,
            type=type,
            model=model,
            input=input,
            output=output,
            extra_metadata=metadata,
            status="completed" if has_output else "in_progress",
            started_at=started,
            ended_at=now if has_output else None,
            latency_ms=(now - started).total_seconds() * 1000 if has_output else None,
            level=level,
        )
        self.db.add(span)
        await self.db.commit()
        await self.db.refresh(span)
        return span

    async def complete_span(
        self,
        span_id: str,
        output: dict | None = None,
        usage: dict | None = None,
        error_message: str | None = None,
    ) -> Span | None:
        result = await self.db.execute(select(Span).where(Span.id == span_id))
        span = result.scalar_one_or_none()
        if span is None:
            return None

        now = datetime.utcnow()
        span.ended_at = now
        if span.started_at:
            span.latency_ms = (now - span.started_at).total_seconds() * 1000
        if output is not None:
            span.output = output
        if usage is not None:
            span.usage = usage
        if error_message:
            span.status = "error"
            span.error_message = error_message
        else:
            span.status = "completed"

        await self.db.commit()
        await self.db.refresh(span)
        return span

    async def get_spans_for_trace(self, trace_id: str) -> list[Span]:
        result = await self.db.execute(
            select(Span)
            .options(selectinload(Span.generations))
            .where(Span.trace_id == trace_id)
            .order_by(Span.started_at)
        )
        return list(result.scalars().all())

    # ============================
    # Generation
    # ============================

    async def create_generation(
        self,
        span_id: str,
        model: str,
        prompt: list | None = None,
        completion: str | None = None,
        usage: dict | None = None,
        cost: float | None = None,
        latency_ms: float | None = None,
        metadata: dict | None = None,
    ) -> Generation:
        gen = Generation(
            id=gen_uuid(),
            span_id=span_id,
            model=model,
            prompt=prompt,
            completion=completion,
            usage=usage,
            cost=cost,
            latency_ms=latency_ms,
            extra_metadata=metadata,
        )
        self.db.add(gen)

        # 自动完成父 Span（有 Generation 说明已经产生输出）
        result = await self.db.execute(select(Span).where(Span.id == span_id))
        parent_span = result.scalar_one_or_none()
        if parent_span and parent_span.status == "in_progress":
            now = datetime.utcnow()
            parent_span.status = "completed"
            parent_span.ended_at = now
            if parent_span.started_at:
                parent_span.latency_ms = (now - parent_span.started_at).total_seconds() * 1000

        await self.db.commit()
        await self.db.refresh(gen)
        return gen

    # ============================
    # Replay
    # ============================

    async def get_trace_replay(self, trace_id: str) -> list[dict]:
        spans = await self.get_spans_for_trace(trace_id)
        events = []
        for span in spans:
            events.append({
                "timestamp": span.started_at.isoformat() if span.started_at else None,
                "type": f"span_{span.type}",
                "name": span.name,
                "input": span.input,
                "output": span.output,
                "status": span.status,
                "latency_ms": span.latency_ms,
            })
            for gen in span.generations:
                events.append({
                    "timestamp": span.started_at.isoformat() if span.started_at else None,
                    "type": "generation",
                    "model": gen.model,
                    "prompt": gen.prompt,
                    "completion": gen.completion,
                    "usage": gen.usage,
                    "cost": gen.cost,
                })
        events.sort(key=lambda e: e.get("timestamp") or "")
        return events
