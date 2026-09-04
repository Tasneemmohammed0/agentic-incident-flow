import asyncio

import pytest

from app.repositories.idempotency import IdempotencyStore, ProcessingStatus


@pytest.fixture
def store() -> IdempotencyStore:
    return IdempotencyStore()


@pytest.mark.asyncio
async def test_first_claim_succeeds(store: IdempotencyStore) -> None:
    assert await store.claim("INC0001") is True
    assert await store.status("INC0001") is ProcessingStatus.PROCESSING


@pytest.mark.asyncio
async def test_duplicate_claim_is_rejected(store: IdempotencyStore) -> None:
    assert await store.claim("INC0001") is True
    assert await store.claim("INC0001") is False


@pytest.mark.asyncio
async def test_claim_after_completion_is_rejected(store: IdempotencyStore) -> None:
    await store.claim("INC0001")
    await store.complete("INC0001")

    assert await store.status("INC0001") is ProcessingStatus.COMPLETED
    assert await store.claim("INC0001") is False


@pytest.mark.asyncio
async def test_release_allows_reclaim(store: IdempotencyStore) -> None:
    await store.claim("INC0001")
    await store.release("INC0001")

    assert await store.status("INC0001") is None
    assert await store.claim("INC0001") is True


@pytest.mark.asyncio
async def test_release_of_unknown_incident_is_a_no_op(store: IdempotencyStore) -> None:
    # Should not raise even though "INC9999" was never claimed.
    await store.release("INC9999")
    assert await store.status("INC9999") is None


@pytest.mark.asyncio
async def test_status_of_unknown_incident_is_none(store: IdempotencyStore) -> None:
    assert await store.status("does-not-exist") is None


@pytest.mark.asyncio
async def test_independent_incidents_do_not_interfere(store: IdempotencyStore) -> None:
    assert await store.claim("INC0001") is True
    assert await store.claim("INC0002") is True
    assert await store.status("INC0001") is ProcessingStatus.PROCESSING
    assert await store.status("INC0002") is ProcessingStatus.PROCESSING


@pytest.mark.asyncio
async def test_concurrent_claims_only_one_winner(store: IdempotencyStore) -> None:
    results = await asyncio.gather(*(store.claim("INC0001") for _ in range(50)))

    assert results.count(True) == 1
    assert results.count(False) == 49
    assert await store.status("INC0001") is ProcessingStatus.PROCESSING


@pytest.mark.asyncio
async def test_concurrent_claims_across_different_incidents_all_win(
    store: IdempotencyStore,
) -> None:
    """Concurrency should only serialize access, not block unrelated claims."""
    incident_ids = [f"INC{i:04d}" for i in range(20)]

    results = await asyncio.gather(*(store.claim(iid) for iid in incident_ids))

    assert all(results)
    for iid in incident_ids:
        assert await store.status(iid) is ProcessingStatus.PROCESSING
