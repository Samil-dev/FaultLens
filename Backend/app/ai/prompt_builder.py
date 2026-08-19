from app.models.faultlens_context import FaultLensContext
from app.models.resilience_analysis import ResilienceAnalysis


class PromptBuilder:
    """
    Builds structured prompts for resilience analysis.
    """

    def build(
        self,
        analysis: ResilienceAnalysis,
        experiment_type: str = "service_down",
        target_node: str | None = None,
        context: FaultLensContext | None = None,
    ) -> str:
        """
        Converts a resilience analysis into a structured prompt.

        experiment_type is included so that AI providers can tailor their
        response to the specific failure mode that was simulated.
        target_node is included so providers can reference the injection point.

        `context`, when provided, is the full FaultLensContext for this
        experiment (system topology + propagation path + history) — it's
        prepended to the prompt so a provider reasons over the whole
        workflow instead of this single analysis in isolation. Optional so
        every existing call site keeps working unchanged.
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

        target_info = f"\nTarget node: {target_node}" if target_node else ""

        context_section = self._build_context_section(context)

        return f"""
You are analyzing the resilience of a software system after a chaos experiment.
{context_section}
Experiment type: {experiment_type}{target_info}

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

    def _build_context_section(self, context: FaultLensContext | None) -> str:
        """
        Renders the system topology + propagation path + trend history from
        a FaultLensContext as a short prose block. Returns an empty string
        when no context was supplied, so `build()` degrades gracefully.
        """

        if context is None:
            return ""

        node_names = ", ".join(node.name for node in context.nodes) or "None"
        propagation = (
            " -> ".join(context.propagation_path)
            if context.propagation_path
            else "N/A (no propagation recorded yet)"
        )

        if context.history:
            trend = "\n".join(
                f"- {entry.created_at}: {entry.experiment_type} on '{entry.target_node}' "
                f"-> resilience score {entry.resilience_score:.1f}, risk {entry.risk_level}"
                for entry in context.history
            )
        else:
            trend = "- No prior experiments recorded for this system."

        return f"""
System: {context.system_name} ({len(context.nodes)} nodes: {node_names})
Propagation path (origin -> affected, in order): {propagation}

Recent experiment history for this system:
{trend}
"""
