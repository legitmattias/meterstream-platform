import pytest
from fastapi import HTTPException

from src.main import get_customer_id


def test_get_customer_id_with_header():
    # When X-Customer-ID is provided it should return that value
    cid = get_customer_id(x_customer_id="cust-123", x_user_role=None)
    assert cid == "cust-123"


def test_get_customer_id_admin_role_allows_none():
    # Admin role may omit the customer header and receive None (global view)
    cid = get_customer_id(x_customer_id=None, x_user_role="admin")
    assert cid is None


def test_get_customer_id_internal_role_allows_none_case_insensitive():
    cid = get_customer_id(x_customer_id=None, x_user_role="InTeRnAl")
    assert cid is None


def test_get_customer_id_missing_raises_403():
    # No header and no admin/internal role -> should raise HTTPException 403
    with pytest.raises(HTTPException) as excinfo:
        get_customer_id(x_customer_id=None, x_user_role=None)
    assert excinfo.value.status_code == 403
