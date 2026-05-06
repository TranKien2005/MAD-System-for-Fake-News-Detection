"""Judge agent (qualitative-first final verdict)."""

import json
from typing import Any

from langchain_core.messages import HumanMessage

from prompts.templates import JUDGE_PROMPT_BASE, DEFAULT_JUDGE_OUTPUT_INSTRUCTIONS
from agents.evaluator import format_knowledge_base
from utils.rate_limit import safe_invoke


def judge(state: dict, llm) -> dict:
    kb_text = format_knowledge_base(state.get("knowledge_base", []), state.get("source_scores", {}))

    full_history = _format_full_debate_with_evaluator(
        state.get("debate_history", []),
        state.get("evaluator_rulings", []),
    )

    output_instructions = state.get("custom_output_instructions") or DEFAULT_JUDGE_OUTPUT_INSTRUCTIONS

    prompt = JUDGE_PROMPT_BASE.format(
        original_news=state["original_news"],
        knowledge_base=kb_text,
        full_debate_with_evaluator=full_history,
        output_format_instructions=output_instructions
    )

    response = safe_invoke(llm, [HumanMessage(content=prompt)])
    verdict = _parse_verdict(response.content)

    return {"verdict": verdict}


def _format_full_debate_with_evaluator(debate_history: list, evaluator_rulings: list) -> str:
    if not debate_history:
        return "(Không có lịch sử tranh luận)"

    rulings_by_round = {}
    for ruling in evaluator_rulings:
        r_num = ruling.get("round_number", 0)
        rulings_by_round[r_num] = ruling

    lines = []
    for r in debate_history:
        r_num = r["round_number"]
        lines.append(f"\n{'=' * 60}")
        lines.append(f"VÒNG {r_num}")
        lines.append(f"{'=' * 60}")
        lines.append("\n📗 DEFENDER:")
        lines.append(r["defender_argument"])
        lines.append("\n📕 CHALLENGER:")
        lines.append(r["challenger_argument"])

        if r_num in rulings_by_round:
            ruling = rulings_by_round[r_num]
            lines.append(f"\n⚖️ THẨM ĐỊNH SAU VÒNG {r_num}:")
            for d in ruling.get("claim_decisions", []):
                lines.append(
                    f"- {d.get('claim_id', '?')}: {d.get('status', 'ACTIVE')} | "
                    f"{d.get('closure_reason', '')}"
                )

            summary = ruling.get("round_summary", "")
            if summary:
                lines.append(f"  📝 Tóm tắt: {summary}")

    return "\n".join(lines)


def _parse_verdict(raw_text: Any) -> dict:
    if not raw_text:
        return {
            "truth_score": 0.5,
            "reasoning": "ERROR: Judge returned empty response. Check model availability or context length."
        }

    if isinstance(raw_text, list):
        text = "".join([c.get("text", "") for c in raw_text if isinstance(c, dict)])
    else:
        text = str(raw_text)
        
    text = text.strip()

    # Nếu rỗng sau khi strip
    if not text:
        return {
            "truth_score": 0.5,
            "reasoning": "ERROR: Judge returned empty/whitespace-only response."
        }

    if text.startswith("```"):
        lines = text.split("\n")
        # Kiểm tra xem có đủ dòng để cắt không
        if len(lines) > 2:
            text_cleaned = "\n".join(lines[1:-1])
            # Thử parse JSON từ phần đã cắt
            try:
                data = json.loads(text_cleaned)
                return _validate_data(data, text)
            except:
                pass

    # Thử parse toàn bộ văn bản là JSON
    try:
        data = json.loads(text)
        return _validate_data(data, text)
    except json.JSONDecodeError:
        pass

    # Cách 1: Tìm dấu ngoặc nhọn (JSON bọc trong văn bản)
    import re
    json_match = re.search(r'(\{.*\})', text, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(1))
            return _validate_data(data, text)
        except json.JSONDecodeError:
            pass

    # Cách 2: Regex quét thủ công điểm số và lý do
    data = {}
    
    # Quét truth_score (hỗ trợ cả dạng "truth_score": 1.0 hoặc "Score: 1.0")
    score_patterns = [
        r'"truth_score":\s*(0\.0|1\.0|0|1|0\.5)',
        r'truth_score\s*[:=]\s*(0\.0|1\.0|0|1|0\.5)',
        r'score\s*[:=]\s*(0\.0|1\.0|0|1|0\.5)'
    ]
    for pattern in score_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                data["truth_score"] = float(match.group(1))
                break
            except:
                continue
    
    # Quét reasoning
    reason_patterns = [
        r'"reasoning":\s*"(.*?)"',
        r'reasoning\s*[:=]\s*(.*)'
    ]
    for pattern in reason_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            data["reasoning"] = match.group(1).strip()
            break

    return _validate_data(data, text)


def _validate_data(data: dict, original_text: str) -> dict:
    """Đảm bảo dữ liệu có đầy đủ các trường cần thiết, nếu không thì tung lỗi."""
    if not isinstance(data, dict):
        raise ValueError(f"Judge output không phải là JSON hợp lệ. Nội dung: {original_text[:200]}...")

    # BẮT BUỘC phải có truth_score
    if "truth_score" not in data:
        raise ValueError(f"Không thể tìm thấy 'truth_score' trong kết quả của Judge. Nội dung: {original_text[:200]}...")
    
    try:
        data["truth_score"] = float(data["truth_score"])
    except (ValueError, TypeError):
        raise ValueError(f"Giá trị 'truth_score' không hợp lệ: {data.get('truth_score')}")
        
    if not data.get("reasoning"):
        data["reasoning"] = "(No reasoning provided by Judge)"
        
    return data
