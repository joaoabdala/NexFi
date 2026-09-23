from datetime import date
from decimal import Decimal

from app.models.enums import TransactionStatus, TransactionType
from app.models.transaction import Transaction
from app.repositories import transaction_repository
from app.schemas.transaction import TransactionFilters


def _make_transaction(db, account, description, competence_date, category=None):
    txn = Transaction(
        user_id=account.user_id,
        account_id=account.id,
        category_id=category.id if category else None,
        description=description,
        type=TransactionType.DESPESA,
        amount=Decimal("10.00"),
        competence_date=competence_date,
        payment_date=competence_date,
        status=TransactionStatus.CONFIRMADA,
        origin="MANUAL",
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn


def test_listing_is_ordered_from_most_recent_to_oldest(db, account):
    _make_transaction(db, account, "Mais antiga", date(2026, 1, 1))
    _make_transaction(db, account, "Do meio", date(2026, 6, 1))
    _make_transaction(db, account, "Mais recente", date(2026, 12, 1))

    items, total = transaction_repository.search(
        db, account.user_id, TransactionFilters(page=1, page_size=20)
    )

    assert total == 3
    assert [i.description for i in items] == ["Mais recente", "Do meio", "Mais antiga"]


def test_same_date_transactions_have_stable_deterministic_order(db, account):
    """Sem desempate, lançamentos no mesmo dia ficam em ordem indefinida pelo SQL —
    o mais recentemente criado deve aparecer primeiro, de forma consistente entre chamadas."""
    same_day = date(2026, 7, 28)
    first = _make_transaction(db, account, "Lançado primeiro", same_day)
    second = _make_transaction(db, account, "Lançado depois", same_day)
    third = _make_transaction(db, account, "Lançado por último", same_day)

    items_1, _ = transaction_repository.search(
        db, account.user_id, TransactionFilters(page=1, page_size=20)
    )
    items_2, _ = transaction_repository.search(
        db, account.user_id, TransactionFilters(page=1, page_size=20)
    )

    ids_1 = [i.id for i in items_1]
    ids_2 = [i.id for i in items_2]
    assert ids_1 == ids_2, "a ordenação deve ser determinística entre chamadas repetidas"
    assert ids_1 == [third.id, second.id, first.id]


def test_pagination_does_not_skip_or_duplicate_rows_with_tied_dates(db, account):
    same_day = date(2026, 7, 28)
    created = [_make_transaction(db, account, f"Lançamento {i}", same_day) for i in range(5)]

    page1, total = transaction_repository.search(
        db, account.user_id, TransactionFilters(page=1, page_size=2)
    )
    page2, _ = transaction_repository.search(
        db, account.user_id, TransactionFilters(page=2, page_size=2)
    )
    page3, _ = transaction_repository.search(
        db, account.user_id, TransactionFilters(page=3, page_size=2)
    )

    assert total == 5
    all_ids = [i.id for i in page1] + [i.id for i in page2] + [i.id for i in page3]
    assert len(all_ids) == len(set(all_ids)) == 5
    assert set(all_ids) == {t.id for t in created}
