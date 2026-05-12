import argparse
import asyncio
import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backends.hf_probe_backend import HuggingFaceProbeAwareBackend


async def main(args) -> None:
    backend = HuggingFaceProbeAwareBackend(
        model=args.model,
        device=args.device,
        torch_dtype=args.torch_dtype,
        probe_layer=args.layer,
        probe_threshold=args.threshold,
        probe_weights_path=args.probe_weights,
    )
    snapshot = await backend.inspect_hidden_states(args.prompt, include_vector=False)
    probe = await backend.probe_tool_intent(
        args.prompt,
        candidate_labels=args.candidates,
        layer_index=args.layer,
        threshold=args.threshold,
    )
    print(
        json.dumps(
            {
                "model": args.model,
                "snapshot": {
                    "layer_index": snapshot.layer_index,
                    "layer_count": snapshot.layer_count,
                    "sequence_length": snapshot.sequence_length,
                    "hidden_size": snapshot.hidden_size,
                    "shape": snapshot.shape,
                },
                "probe": {
                    "should_route": probe.should_route,
                    "confidence": probe.confidence,
                    "label": probe.label,
                    "selected_candidate": probe.selected_candidate,
                    "notes": probe.notes,
                },
            },
            indent=2,
        )
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Inspect hidden states with the Hugging Face probe-aware backend."
    )
    parser.add_argument("--model", default="distilgpt2")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--torch-dtype", default="auto")
    parser.add_argument("--layer", type=int, default=-1)
    parser.add_argument("--threshold", type=float, default=0.72)
    parser.add_argument("--probe-weights", type=Path)
    parser.add_argument(
        "--prompt",
        default="/debug GPU tray reseat boot failure",
    )
    parser.add_argument(
        "--candidates",
        nargs="*",
        default=["gpu-tray-reseat", "psu-led-status"],
    )
    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(main(parse_args()))
