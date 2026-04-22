from __future__ import annotations

from app.models.domain import AnalysisItem, GapAnalysisResult, JDProfile, ResumeFacts


class GapAnalysisService:
    def analyze(self, resume_facts: ResumeFacts, jd_profile: JDProfile) -> GapAnalysisResult:
        fact_texts = [text.lower() for text in resume_facts.all_fact_texts()]
        highlights: list[AnalysisItem] = []
        gaps: list[AnalysisItem] = []
        suggestions: list[AnalysisItem] = []

        matched_keywords = []
        missing_keywords = []

        for keyword in jd_profile.keywords[:10]:
            if any(keyword.lower() in fact for fact in fact_texts):
                matched_keywords.append(keyword)
            else:
                missing_keywords.append(keyword)

        if matched_keywords:
            highlights.append(
                AnalysisItem(
                    title="关键词匹配",
                    detail=f"简历中已覆盖这些 JD 关键词：{', '.join(matched_keywords[:8])}",
                    supporting_facts=[
                        fact for fact in resume_facts.all_fact_texts()
                        if any(keyword.lower() in fact.lower() for keyword in matched_keywords[:4])
                    ][:4],
                )
            )

        if resume_facts.experience:
            highlights.append(
                AnalysisItem(
                    title="已有经历可支撑目标岗位",
                    detail="简历包含可用于对齐 JD 的工作/项目经历，可在改写时前置展示。",
                    supporting_facts=[fact.text for fact in resume_facts.experience[:3]],
                )
            )

        if missing_keywords:
            gaps.append(
                AnalysisItem(
                    title="JD 关键词覆盖不足",
                    detail=f"以下关键词未在原始简历中显式出现：{', '.join(missing_keywords[:8])}",
                    supporting_facts=[],
                )
            )

        if not resume_facts.achievements:
            gaps.append(
                AnalysisItem(
                    title="结果量化信息偏少",
                    detail="原始简历中未明显识别出成果、指标或奖项，改写时只能保守强化表述。",
                    supporting_facts=[],
                )
            )

        suggestions.append(
            AnalysisItem(
                title="重排信息顺序",
                detail="优先展示与 JD 直接相关的经历、技能和项目，降低不相关内容的篇幅。",
                supporting_facts=[fact.text for fact in resume_facts.experience[:2] + resume_facts.projects[:2]],
            )
        )
        suggestions.append(
            AnalysisItem(
                title="补全显式关键词",
                detail="仅在原始事实已支持的前提下，把 JD 中的重要术语改写为更接近招聘语境的表达。",
                supporting_facts=matched_keywords[:5],
            )
        )

        constraints = [
            "禁止新增未在原始简历中出现的公司、学校、项目、技术栈、奖项、时间线或量化指标。",
            "若 JD 要求在原始简历中没有事实支撑，只能标记为缺口，不可伪造补齐。",
            "最终改写必须等待用户确认后执行。",
        ]

        return GapAnalysisResult(
            highlights=highlights,
            gaps=gaps,
            suggestions=suggestions,
            fact_constraints=constraints,
            trace={
                "matched_keywords": matched_keywords,
                "missing_keywords": missing_keywords,
                "resume_fact_count": len(resume_facts.all_fact_texts()),
            },
        )
