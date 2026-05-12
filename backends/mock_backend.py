import re

from backends.base import ModelBackend


class MockBackend(ModelBackend):
    """Deterministic backend for tests, demos, and CI without a local model."""

    name = "mock"

    async def generate(self, prompt: str) -> str:
        if "Return ONLY the page_id" in prompt:
            return self._select_candidate_page(prompt)

        return self._answer_from_context(prompt)

    def _select_candidate_page(self, prompt: str) -> str:
        candidate_ids = re.findall(r"page_id:\s*([a-z0-9-]+)", prompt)
        query_match = re.search(r"USER QUERY:\s*(.+)", prompt, re.IGNORECASE | re.DOTALL)
        query = query_match.group(1).lower() if query_match else ""

        if any(term in query for term in ["psu", "power", "amber"]) and "psu-led-status" in candidate_ids:
            return "psu-led-status"
        if "gpu" in query and "gpu-tray-reseat" in candidate_ids:
            return "gpu-tray-reseat"
        if "network" in query and "network-boot-failure" in candidate_ids:
            return "network-boot-failure"
        if "bmc" in query and "bmc-reset-procedure" in candidate_ids:
            return "bmc-reset-procedure"
        if "memory" in query and "memory-training-failure" in candidate_ids:
            return "memory-training-failure"

        return candidate_ids[0] if candidate_ids else ""

    def _answer_from_context(self, prompt: str) -> str:
        page_ids = set(re.findall(r"PAGE_ID:\s*([a-z0-9-]+)", prompt))

        if "gpu-tray-reseat" in page_ids:
            return (
                "Check the GPU tray alignment first, then verify auxiliary GPU "
                "power leads and confirm the PSU LEDs are in a healthy state. "
                "If the system still fails to boot, compare BMC event entries "
                "against the reseat timestamp and stop before replacing parts "
                "unless the wiki context supports that step. Sources: "
                "gpu-tray-reseat, psu-led-status."
            )

        if "network-boot-failure" in page_ids:
            return (
                "Start with link state and boot target validation, then confirm "
                "that the expected VLAN and PXE policy are assigned. Sources: "
                "network-boot-failure."
            )

        if page_ids:
            ordered = ", ".join(sorted(page_ids))
            return (
                "Use the retrieved technician wiki context to follow the known "
                f"procedure and avoid unsupported steps. Sources: {ordered}."
            )

        return (
            "The retrieved context is insufficient to answer safely. Search the "
            "wiki again with a more specific symptom, component, or event code."
        )
