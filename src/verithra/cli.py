import argparse
import sys
from pathlib import Path

from verithra.config import Settings, VerithraError
from verithra.indexing import build_index
from verithra.rag.grounding import ABSTENTION_MESSAGE
from verithra.rag.pipeline import Pipeline
from verithra.retrieval.faiss_index import FaissIndex
from verithra.runtime import clients, index_directory, parameters


def main() -> int:
    parser = argparse.ArgumentParser(description="Verithra technical support assistant")
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build-index", help="Build the local knowledge index")
    build.add_argument("--corpus", type=Path, default=Path("data/raw"))
    build.add_argument("--cases", type=Path, default=Path("data/support_cases/cases.jsonl"))
    build.add_argument("--demo", action="store_true", help="Run without API calls")
    ask = commands.add_parser("ask", help="Answer an issue using the saved index")
    ask.add_argument("question")
    ask.add_argument("--demo", action="store_true", help="Run without API calls")
    args = parser.parse_args()
    try:
        settings = Settings.from_env()
        config = parameters(args.demo, settings)
        embedder, generator = clients(args.demo, settings)
        directory = index_directory(args.demo)
        if args.command == "build-index":
            index = build_index(
                args.corpus, directory, embedder, config.chunk_size, config.overlap, args.cases
            )
            index.save(directory, vars(config))
            print(f"Saved {len(index.chunks)} passages to {directory}")
            return 0
        pipeline = Pipeline(
            FaissIndex.load(directory),
            embedder,
            generator,
            config.top_k,
            config.threshold,
            settings.max_context_characters,
        )
        result = pipeline.ask(args.question)
        print(result.support_status)
        if result.support_status == "INSUFFICIENT_EVIDENCE":
            print(ABSTENTION_MESSAGE)
            return 0
        print("Issue:", result.interpretation)
        print("Likely cause:", result.likely_cause)
        for number, step in enumerate(result.recommended_steps, 1):
            print(f"{number}. {step.text}")
        for source in result.sources:
            print(f"Source: {source.title} / {source.section} [{source.chunk_id}]")
        return 0
    except VerithraError as exc:
        print(f"Verithra: {exc}", file=sys.stderr)
        return 1
    except (OSError, ValueError):
        print(
            "Verithra: Cannot read local knowledge. Check files and rebuild the index.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
