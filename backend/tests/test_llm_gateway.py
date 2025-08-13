import os
import sys
import asyncio


def _ensure_backend_on_syspath() -> None:
	"""Ensure `backend` is importable so we can import `app.*` modules."""
	current_dir = os.path.dirname(__file__)
	backend_dir = os.path.abspath(os.path.join(current_dir, ".."))
	if backend_dir not in sys.path:
		sys.path.insert(0, backend_dir)


async def main() -> None:
	_ensure_backend_on_syspath()
	from app.services.llm_gateway import LLMGateway

	gateway = LLMGateway()
	response = await gateway.get_completion(
		system_prompt="你是一个简洁的助教。",
		messages=[
			{"role": "user", "content": "请用一句话解释二分查找。"},
		],
		max_tokens=256,
		temperature=0.3,
	)
	print("\n=== LLM reply ===\n")
	print(response)


if __name__ == "__main__":
	asyncio.run(main())


