from app.ai.prompt_builder import PromptBuilder
from app.ai.providers.base import BaseAIProvider
from app.models.ai_analysis import AIAnalysis
from app.models.faultlens_context import FaultLensContext
from app.models.resilience_analysis import ResilienceAnalysis


class AIAnalyzer:
    """
    Coordinates resilience analysis with an AI provider.
    """

    def __init__(
        self,
        provider: BaseAIProvider
    ):
        self.provider = provider
        self.prompt_builder = PromptBuilder()

    def analyze(
        self,
        resilience_analysis: ResilienceAnalysis,
        experiment_type: str = "service_down",
        target_node: str | None = None,
        context: FaultLensContext | None = None,
    ) -> AIAnalysis:
        """
        Generates an AI interpretation of the resilience analysis.

        `context`, when provided, grounds the prompt in the full FaultLens
        workflow (system topology, propagation path, experiment history)
        instead of just this one analysis — see PromptBuilder.build().
        """

        prompt = self.prompt_builder.build(
            resilience_analysis,
            experiment_type=experiment_type,
            target_node=target_node,
            context=context,
        )

        response = self.provider.generate(prompt)

        root_cause = self._build_root_cause(
            resilience_analysis, experiment_type, target_node
        )
        risk_interpretation = self._build_risk_interpretation(
            resilience_analysis, experiment_type
        )

        return AIAnalysis(
            summary=response,
            root_cause=root_cause,
            risk_interpretation=risk_interpretation,
            recommendations=[
                recommendation.description
                for recommendation in resilience_analysis.recommendations
            ],
            confidence=0.85,
            provider=self.provider.name,
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    def _build_root_cause(
        self,
        analysis: ResilienceAnalysis,
        experiment_type: str,
        target_node: str | None,
    ) -> str:
        """
        Builds an evidence-based root cause string from the actual analysis.
        """
        node_label = f"node '{target_node}'" if target_node else "the target node"
        blast = analysis.impact.blast_radius
        affected = analysis.impact.affected_nodes

        _root_cause_templates: dict[str, str] = {
            "service_down": (
                f"Complete failure of {node_label} caused {affected} downstream "
                f"service(s) to lose connectivity, producing a blast radius of "
                f"{blast:.0%}. The dependency chain amplified the outage beyond "
                "the single point of failure."
            ),
            "latency_spike": (
                f"Elevated latency injected at {node_label} propagated through "
                f"{affected} synchronous dependency chain(s) (blast radius "
                f"{blast:.0%}), multiplying end-to-end response times across "
                "the call graph."
            ),
            "resource_exhaustion": (
                f"CPU and memory saturation at {node_label} reduced processing "
                f"capacity, causing {affected} dependent service(s) to queue "
                f"requests and raise error rates (blast radius {blast:.0%})."
            ),
            "traffic_spike": (
                f"Sudden request-volume overload at {node_label} exhausted "
                f"connection and thread pools, driving error rates up and "
                f"cascading elevated latency to {affected} downstream service(s) "
                f"(blast radius {blast:.0%})."
            ),
        }

        return _root_cause_templates.get(
            experiment_type,
            (
                f"The observed degradation originated at {node_label} and "
                f"propagated to {affected} service(s) (blast radius {blast:.0%}) "
                "via the dependency structure."
            ),
        )

    def _build_risk_interpretation(
        self,
        analysis: ResilienceAnalysis,
        experiment_type: str,
    ) -> str:
        """
        Builds an evidence-based risk interpretation from the actual analysis.
        """
        level = analysis.risk.level
        avg_recovery = analysis.recovery.average_recovery_seconds
        max_recovery = analysis.recovery.max_recovery_seconds
        failed = analysis.recovery.failed_recoveries
        blast = analysis.impact.blast_radius

        failed_clause = (
            f" {len(failed)} node(s) failed to recover entirely."
            if failed
            else " All affected nodes recovered successfully."
        )

        return (
            f"The {experiment_type.replace('_', ' ')} experiment produced a "
            f"'{level}' risk classification with a {blast:.0%} blast radius. "
            f"Average recovery time was {avg_recovery:.1f}s "
            f"(max {max_recovery:.1f}s).{failed_clause} "
            f"Reason: {analysis.risk.reason}"
        )