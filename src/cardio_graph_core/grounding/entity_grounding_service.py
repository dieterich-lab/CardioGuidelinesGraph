from __future__ import annotations

from typing import Any, Optional, Tuple

from cardio_graph_core.extraction.guideline_graph_builder import GuidelineGraphBuilder


class EntityGroundingService(GuidelineGraphBuilder):
    """Dedicated service facade for entity grounding.

    This keeps the grounding API separate from extraction/e2e orchestration while
    reusing the current proven grounding implementation in GuidelineGraphBuilder.
    """

    def ground_entity(
        self,
        term: str,
        role: Optional[str],
        query_context: Any = None,
    ) -> Tuple[Optional[int], Optional[str], float]:
        return self._search_best_concept(
            term,
            role,
            query_context=query_context,
        )

    def get_concept_term(self, concept_id_value: Any) -> str:
        if not concept_id_value:
            return ""
        try:
            concept_id_int = int(concept_id_value)
        except (TypeError, ValueError):
            return ""
        return self._get_preferred_term(concept_id_int) or ""

    def close(self) -> None:
        if self.vector_retriever and hasattr(self.vector_retriever, "close"):
            self.vector_retriever.close()
        if self.snomed_explorer and hasattr(self.snomed_explorer, "close"):
            self.snomed_explorer.close()
