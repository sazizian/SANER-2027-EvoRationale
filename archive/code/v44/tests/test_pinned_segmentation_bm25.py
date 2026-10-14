"""Higher-fidelity search and tokenizer-specific checks in the offline environment."""
from copy import deepcopy
from evorationale.segmentation import segment_text
from evorationale.retrieval import LocalHybridRetriever
from evorationale.model import normalize_artifact


class FakeFastTokenizer:
    is_fast = True
    def __call__(self, text, **kwargs):
        assert kwargs['add_special_tokens'] is False
        assert kwargs['return_offsets_mapping'] is True
        return {'offset_mapping': [(i,i+1) for i,c in enumerate(text) if c.isalnum()]}


def test_fast_tokenizer_bounded_segments():
    tokenizer = FakeFastTokenizer()
    parts = segment_text('abc d\nef ghi jkl mn op', 'r::a::v', max_tokens=10,
                         overlap=3, tokenizer=tokenizer)
    assert len(parts) > 2
    for part in parts:
        assert len(tokenizer(part.text, add_special_tokens=False,
                             return_offsets_mapping=True)['offset_mapping']) <= 8
        assert part.text


def test_bm25_rewards_genuine_term_frequency(approved_state, history):
    example = next(a for a in history if a['artifact_id'] == 'inc-017')
    docs = []
    for index, content in enumerate(('cache sentinel filler filler filler filler filler filler',
                                     'cache cache cache cache sentinel filler filler filler'), 1):
        a=deepcopy(example)
        a.update(artifact_id=f'bm25-{index}', content=content, tags=[], title='matched query')
        a.pop('content_sha256'); a.pop('version_id')
        docs.append(normalize_artifact(a))
    retriever=LocalHybridRetriever()
    retriever.index(docs)
    answer=retriever.search(approved_state, {'query': 'cache'}, limit=2)
    assert answer[0]['artifact_id'] == 'bm25-2'
