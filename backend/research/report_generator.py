# backend/research/report_generator.py
"""ResearchReportGenerator: produces evidence-driven research reports."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse

from backend.research.schemas import ResearchState


class ResearchReportGenerator:
    """Generates structured research reports from collected evidence."""

    async def generate(
        self, state: ResearchState, tenant_id: int, user_id: int,
    ) -> dict:
        """Generate a markdown research report with evidence bindings."""
        from langchain.chat_models import init_chat_model
        from backend.config import get_settings
        settings = get_settings()

        plan = state.plan
        if not plan:
            return {}

        # Build evidence index
        evidence_by_task: dict[str, list] = {}
        for ev in state.evidence:
            evidence_by_task.setdefault(ev.task_id, []).append(ev)

        # Build task results summary and a global evidence map.
        # Evidence tags must be globally unique; otherwise the LLM may emit
        # duplicate references such as multiple "[证据1]" entries.
        tasks_summary = ""
        evidence_map = {}
        evidence_counter = 0
        for task in plan.tasks:
            finding = state.task_results.get(task.task_id, {}).get("finding", "No results")
            tasks_summary += f"\n### {task.name}\n\n{finding}\n"
            task_evidence = evidence_by_task.get(task.task_id, [])
            for ev in task_evidence:
                evidence_counter += 1
                tag = f"[证据{evidence_counter}]"
                evidence_map[tag] = self._format_reference(ev)
                tasks_summary += f"\n> **{tag}** ({ev.confidence.value} 置信度): {ev.content[:300]}\n"
                if self._is_valid_citation(ev.citation):
                    tasks_summary += f"> 来源: {ev.citation.strip()}\n"

        # Generate full report via LLM
        model = init_chat_model(
            model="qwen-turbo",
            model_provider="openai",
            api_key=settings.ark_api_key,
            base_url=settings.base_url,
            temperature=0.0,
            max_tokens=4096,
            timeout=60,
        )
        from langchain_core.messages import SystemMessage, HumanMessage

        refs_text = "\n".join(f"- {tag}: {url}" for tag, url in list(evidence_map.items())[:50])

        prompt = f"""根据以下证据生成一份专业的中文研究报告。

研究目标: {plan.goal}

收集的证据和发现:
{tasks_summary[:12000]}

证据来源清单:
{refs_text}

报告结构要求（全部使用中文撰写）:
1. 摘要 (3-5句话概括核心发现)
2. 关键发现 (编号列表，每一条附上证据引用标签如 [证据1])
3. 详细分析 (按主题组织，不是按任务)
4. 影响与建议
5. 局限性与不足
6. 参考文献

重要：每个事实性结论必须标注证据引用标签，如 [证据1]、[证据2]。
不要输出 [source: 1]、source: 2、空项目符号等占位引用；参考文献只能来自“证据来源清单”。
使用 Markdown 格式：## 标题、**加粗**、列表、> 引用证据。"""

        response = await model.ainvoke([
            SystemMessage(content="你是一位资深研究分析师，撰写证据驱动的研究报告。每个结论必须引用证据标签（如[证据1]）。请使用中文撰写。"),
            HumanMessage(content=prompt),
        ])
        content = response.content if hasattr(response, "content") else str(response)
        content = self._replace_references_section(content, evidence_map)

        report_id = f"rpt_{uuid.uuid4().hex[:12]}"

        return {
            "report_id": report_id,
            "execution_id": state.execution_id,
            "title": plan.goal,
            "format": "markdown",
            "content": content,
            "evidence_map": evidence_map,
            "executive_summary": self._extract_summary(content),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def _is_valid_citation(citation: str | None) -> bool:
        """Reject empty or LLM placeholder citations such as 'source: 1'."""
        if not citation:
            return False
        value = citation.strip()
        if not value:
            return False
        if value in {"-", "*", "•", "·"}:
            return False
        lower = value.strip("[]() ").lower()
        if lower.startswith(("source:", "source：", "来源:", "来源：")):
            return False
        if lower in {"source", "citation", "引用", "参考文献", "n/a", "none", "无"}:
            return False
        return True

    def _format_reference(self, ev) -> str:
        """Return a readable reference string, falling back to evidence content."""
        if self._is_valid_citation(ev.citation):
            citation = ev.citation.strip()
            parsed = urlparse(citation)
            if parsed.scheme and parsed.netloc:
                return citation
            return citation
        content = (ev.content or "").strip().replace("\n", " ")
        if not content:
            return f"{ev.source.value} evidence"
        return f"{ev.source.value}: {content[:120]}"

    @staticmethod
    def _replace_references_section(content: str, evidence_map: dict[str, str]) -> str:
        """Replace the model-generated references with deterministic evidence refs."""
        import re

        lines = []
        for tag, ref in evidence_map.items():
            value = str(ref or "").strip()
            if ResearchReportGenerator._is_valid_citation(value):
                lines.append(f"- {tag}: {value}")

        refs = "\n".join(lines)
        if not refs:
            refs = "- 本次研究未收集到可用引用。"

        section = f"## 参考文献\n\n{refs}".strip()
        heading_pattern = re.compile(
            r"(?im)^[ \t]*(?:#{1,6}[ \t]*)?(?:\*\*)?[ \t]*参考文献[ \t]*(?:\*\*)?[ \t]*[:：]?[ \t]*$"
        )
        match = heading_pattern.search(content)
        if match:
            return (content[:match.start()].rstrip() + "\n\n" + section).strip()
        return (content.rstrip() + "\n\n" + section).strip()

    def _extract_summary(self, content: str) -> str:
        """Extract executive summary section from report."""
        import re
        match = re.search(
            r"(?:摘要|Executive Summary)[\s\S]*?(?=##|\Z)",
            content, re.IGNORECASE,
        )
        if match:
            return match.group(0).strip()[:500]
        # Fallback: first paragraph after title
        lines = content.split("\n")
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                return stripped[:500]
        return ""


_generator: ResearchReportGenerator | None = None


def get_report_generator() -> ResearchReportGenerator:
    global _generator
    if _generator is None:
        _generator = ResearchReportGenerator()
    return _generator
