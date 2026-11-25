from fastapi import APIRouter

from backend.provenance.data_provenance import build_event_provenance


router = APIRouter()


@router.get("/optimize/provenance")
def get_provenance():

    import backend.assistant_api as api

    assistant = getattr(api, "assistant", None)

    if assistant is None:
        return {
            "success": False,
            "message": "No event has been created yet."
        }

    state = assistant.engine.get_state()

    return {
        "success": True,
        "provenance": build_event_provenance(state)
    }
