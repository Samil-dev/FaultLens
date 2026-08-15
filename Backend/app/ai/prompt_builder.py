from app.models.resilience_analysis import ResilienceAnalysis


class PromptBuilder:
    """
    Builds structured prompts for resilience analysis.
    """

    def build(
        self,
        analysis: ResilienceAnalysis,
        experiment_type: str = "service_down",
    ) -> str:
        """
        Converts a resilience analysis into a structured prompt.

        experiment_type is included so that AI providers can tailor their
        response to the specific failure mode that was simulated.
        """

        critical_nodes = ", ".join(
            analysis.impact.critical_nodes
        ) or "None"

        recommendations = "\n".join(
            f"- {recommendation.title}: "
            f"{recommendation.description}"
            for recommendation in analysis.recommendations
        ) or "- None"

        failed_recoveries = ", ".join(
            analysis.recovery.failed_recoveries
        ) or "None"

        return f"""
You are analyzing the resilience of a software system after a chaos experiment.

Experiment type: {experiment_type}

Impact:
- Blast radius: {analysis.impact.blast_radius}
- Affected nodes: {analysis.impact.affected_nodes}
- Total nodes: {analysis.impact.total_nodes}
- Critical nodes: {critical_nodes}
- Average metric impact: {analysis.impact.average_metric_impact}

Recovery:
- Recovered nodes: {analysis.recovery.recovered_nodes}
- Total recovery nodes: {analysis.recovery.total_recovery_nodes}
- Average recovery time: {analysis.recovery.average_recovery_seconds} seconds
- Maximum recovery time: {analysis.recovery.max_recovery_seconds} seconds
- Failed recoveries: {failed_recoveries}

Risk:
- Level: {analysis.risk.level}
- Reason: {analysis.risk.reason}

Current recommendations:
{recommendations}

Provide:
1. A concise summary.
2. The most likely root cause.
3. An interpretation of the risk.
4. Additional recommendations.
""".strip()
