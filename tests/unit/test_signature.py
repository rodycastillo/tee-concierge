from tee_concierge.infrastructure.whatsapp.signature import sign, verify_signature


def test_valid_signature_is_accepted() -> None:
    body = b'{"a": 1}'
    assert verify_signature("secret", body, sign("secret", body))


def test_wrong_secret_tampered_body_and_missing_header_are_rejected() -> None:
    body = b'{"a": 1}'
    header = sign("secret", body)
    assert not verify_signature("other", body, header)
    assert not verify_signature("secret", b'{"a": 2}', header)
    assert not verify_signature("secret", body, None)
    assert not verify_signature("", body, header)
