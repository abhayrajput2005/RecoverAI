"""Tool: record_outcome — Store the action and result for analytics."""
from app.audit import log_decision
from app.db import CaseRecord, get_session
from app.models import CaseOutcome


def record_outcome(outcome: CaseOutcome) -> None:
    session = get_session()
    try:
        case = session.query(CaseRecord).filter_by(case_id=outcome.case_id).one_or_none()
        if case is None:
            raise ValueError(f"Unknown case_id: {outcome.case_id}")
        case.status = outcome.status.value
        if outcome.recovered_amount is not None:
            case.recovered_amount = outcome.recovered_amount
        session.commit()
        log_decision(outcome.case_id, "execution", outcome.model_dump(mode="json"))
    finally:
        session.close()
