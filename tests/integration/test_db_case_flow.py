import uuid

import pytest

from medflowai.db import CaseIn, ConsultationIn


@pytest.mark.asyncio
async def test_case_flow(supabase_client):
    # Create a case
    case_id = await supabase_client.create_case(
        CaseIn(
            patient_id=str(uuid.uuid4()),
            specialty="cardiology",
            description="Test case",
        )
    )
    cases = await supabase_client.list_cases()
    assert any(c.id == case_id for c in cases)

    # Add consultation
    cons_id = await supabase_client.add_consultation(
        ConsultationIn(
            case_id=case_id,
            request={"q": "test"},
            response={"a": "ok"},
        )
    )
    consultations = await supabase_client.list_consultations(case_id)
    assert any(c.id == cons_id for c in consultations)
