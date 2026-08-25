import json
from urllib.request import Request, urlopen

from app.core.config import Settings
from app.modules.financial_assistant.schemas import AssistantAnswer
from app.modules.financial_health.schemas import FinancialHealthSummary

DISCLAIMER = "Orientación educativa basada en tus registros; no sustituye asesoría profesional."


def deterministic_answer(summary: FinancialHealthSummary) -> AssistantAnswer:
    if summary.recommendations:
        item = summary.recommendations[0]
        answer = f"{item.title}. {item.detail}"
    else:
        answer = (
            f"Tu estado actual es {summary.status}. Revisa el desglose para conocer los factores."
        )
    return AssistantAnswer(answer=answer, source="rules", disclaimer=DISCLAIMER)


def explain_with_ai(
    settings: Settings, summary: FinancialHealthSummary, question: str
) -> AssistantAnswer:
    if (
        settings.privacy_mode == "strict"
        or not settings.financial_ai_enabled
        or settings.openai_api_key is None
    ):
        return deterministic_answer(summary)
    context = {
        "status": summary.status,
        "score": summary.score,
        "components": [item.model_dump() for item in summary.components],
        "recommendations": [item.model_dump() for item in summary.recommendations],
        "limitations": summary.limitations,
    }
    payload = {
        "model": settings.openai_model,
        "store": False,
        "instructions": (
            "Explica únicamente los resultados entregados. No recalcules, no inventes cifras, "
            "no recomiendes inversiones ni deuda nueva. Responde en español y "
            "menciona limitaciones."
        ),
        "input": (
            f"Pregunta: {question}\nContexto calculado: "
            f"{json.dumps(context, ensure_ascii=False)}"
        ),
        "text": {
            "format": {
                "type": "json_schema",
                "name": "financial_explanation",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {"answer": {"type": "string"}},
                    "required": ["answer"],
                    "additionalProperties": False,
                },
            }
        },
    }
    request = Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode(),
        method="POST",
        headers={
            "Authorization": f"Bearer {settings.openai_api_key.get_secret_value()}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=20) as response:
            result = json.loads(response.read())
        text = next(
            content["text"]
            for output in result.get("output", [])
            if output.get("type") == "message"
            for content in output.get("content", [])
            if content.get("type") == "output_text"
        )
        answer = json.loads(text)["answer"]
        return AssistantAnswer(answer=answer, source="openai", disclaimer=DISCLAIMER)
    except (OSError, KeyError, StopIteration, ValueError, json.JSONDecodeError):
        return deterministic_answer(summary)
