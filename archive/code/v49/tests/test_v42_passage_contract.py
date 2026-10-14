"""Regression tests for v4.2 development-only passage selection and provenance."""
import json
from types import SimpleNamespace

from evorationale.linking import OpenAILinker
from evorationale.evidence_semantics import evidence_spans, direct_relevance
from evorationale.model import element_by_id
from evorationale.verification import EvidenceVerifier


class Reply:
    def __init__(self, value):
        self.value = value
        self.sent = None

    def create(self, **kwargs):
        self.sent = kwargs
        payload = json.loads(kwargs["input"])
        p = payload["artifacts"][0]["passages"][0]
        a = payload["artifacts"][0]["artifact_handle"]
        return SimpleNamespace(output_text=json.dumps({"links": [
            {"artifact_handle": a, "passage_handle": p["passage_handle"],
             "element_id": "A1", "relation": "contradicts",
             "confidence": self.value, "quote": "MODEL FORGED QUOTE"}
        ]}))


def test_model_can_only_select_exact_source_passage(approved_state, history):
    a = next(x for x in history if x["artifact_id"] == "inc-017")
    fake = Reply(0.7)
    linker = OpenAILinker("mock", client=SimpleNamespace(responses=fake))
    props = linker.propose(approved_state, [a], {"id": "q1", "element_id": "A1", "query": "profile updates"})
    assert len(props) == 1
    assert "MODEL FORGED QUOTE" not in props[0]["quote"]
    assert props[0]["quote"] in a["content"]
    verified, rejected = EvidenceVerifier().verify(approved_state, history, props)
    assert verified and not rejected
    assert fake.sent["text"]["format"]["schema"]["properties"]["links"]["items"]["properties"]["passage_handle"]["enum"]


def test_invalid_model_confidence_is_not_normalized(approved_state, history):
    a = next(x for x in history if x["artifact_id"] == "inc-017")
    fake = Reply(9)
    linker = OpenAILinker("mock", client=SimpleNamespace(responses=fake))
    assert linker.propose(approved_state, [a], {"id": "q1", "element_id": "A1", "query": "profile updates"}) == []
    assert linker.last_proposal_rejections == [{"reason": "invalid_model_confidence"}]


def test_wrapped_patch_text_is_verbatim_contiguous():
    content = ("@@ -10,3 +10,5 @@ changes\n"
               "+PodStatus records the resources allocated to the Pod, and\n"
               "+records the actual resources currently applied to containers.\n"
               "+This status allows the kubelet to report a pending resize.\n\n"
               " context")
    spans = evidence_spans(content)
    assert any("PodStatus records" in q and "actual resources" in q and "\n+" in q
               for q in spans)
    assert all(q in content and len(q) <= 650 for q in spans)


def test_design_doc_factual_assertion_is_screened_but_unrelated_is_rejected(approved_state):
    element = {"id": "I1", "element_type": "implementation_scope",
               "text": "PodStatus reports allocated resources for a container"}
    assert direct_relevance(element,
           "PodStatus reports allocated resources for a container.", "supports",
                            allow_descriptive=True)[0]
    assert not direct_relevance(element,
           "The container was mentioned in a generic meeting note.", "supports",
                            allow_descriptive=True)[0]


def test_unrelated_markdown_bullets_are_not_synthetically_conjoined():
    s = "* The target resources are reported to clients.\n* An unrelated logger is changed."
    assert not any("resources" in q and "unrelated" in q for q in evidence_spans(s))
