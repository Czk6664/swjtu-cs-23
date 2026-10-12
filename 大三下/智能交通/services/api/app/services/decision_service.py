from app.models import DecisionSummary


class DecisionService:
    def generate(
        self,
        scene_name: str,
        workflow: str,
        notes: str | None,
        has_forecast: bool,
        has_detection: bool,
    ) -> DecisionSummary:
        facts = [f"场景名称: {scene_name}", f"工作流: {workflow}"]
        if has_forecast:
            facts.append("已纳入交通流预测结果摘要")
        if has_detection:
            facts.append("已纳入目标识别结果摘要")
        if notes:
            facts.append(f"用户备注: {notes}")

        return DecisionSummary(
            facts=facts,
            risk_level="Level II",
            recommendation="建议先进行分级诱导，并同步值守人员关注关键路段。",
            explanation="当前决策层以结构化规则和摘要结果为主，后续将接入真实大模型调用与更完整的推理上下文。",
        )
