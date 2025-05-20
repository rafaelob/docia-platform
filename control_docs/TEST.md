# Test Register
<!-- 
Traceable list of tests.  
Include module, test file, coverage group (unit, integration, e2e), etc.
-->

| Module               | Test File                   | Purpose/Scenario               | Coverage | Created      | Last Run     | Status        | Notes                       |
|----------------------|-----------------------------|--------------------------------|---------|--------------|--------------|---------------|-----------------------------|
| medflowai.adapters    | tests/unit/test_adapters.py | Adapter happy-path & error handling | unit     | 2025-05-10 | *pending* | - | New |
| medflowai.tools.rag_tool | tests/unit/test_rag_tool.py | Retrieval with mock KB | unit     | 2025-05-10 | 2025-05-18 | ✅ Pass | - |
| medflowai.agents.medical_rag | tests/unit/test_medical_rag.py | MedicalRAGAgent success/failure paths | unit | 2025-05-13 | 2025-05-18 | ✅ Pass |
| medflowai.core.divergence | tests/unit/test_divergence.py | Divergence detection rules | unit     | 2025-05-10 | *pending* | - | New |
| medflowai.agents.divergence_review | tests/unit/test_divergence_agent.py | Qualitative equivalence/divergence | unit | 2025-05-10 | *pending* | - | New |
| medflowai.agents.divergence_review | tests/unit/test_divergence_review_agent.py | Clinical equivalence/divergence, retry logic | unit | 2025-05-13 | 2025-05-18 | ✅ Pass | - |
| medflowai.core.orchestrator | tests/integration/test_orchestrator.py | End-to-end flow (happy/divergent) | int      | 2025-05-10 | *pending* | - | New |
| medflowai.core.orchestrator | tests/unit/test_orchestrator_specialist_flow.py | Branching: divergence vs equivalent | unit | 2025-05-18 | 2025-05-18 | ✅ Pass | New |
| medflowai.db.supabase_client | tests/integration/test_db_case_flow.py | CRUD cases + consultations | int | 2025-05-10 | *pending* | - | New |
| arbiter-o3.service | tests/services/test_arbiter_o3_unit.py | Endpoint decision path & schema | unit | 2025-05-19 | 2025-05-19 | ✅ Pass | New |
| medflowai.core.retry_utils | tests/unit/test_retry_utils.py | Back-off logic and error handling | unit | 2025-05-19 | *pending* | - | New |

### Divergence engine
- Test file: `tests/unit/test_divergence.py`
- Coverage target: ≥ 90 %
- Last run: *pending*
