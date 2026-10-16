import httpx


async def _register_guardian(client: httpx.AsyncClient, email: str) -> dict[str, str]:
    resp = await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "gizli-parola-123", "role": "guardian"},
    )
    assert resp.status_code == 201
    login = await client.post(
        "/v1/auth/login", json={"email": email, "password": "gizli-parola-123"}
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def test_register_login_refresh_logout(client: httpx.AsyncClient) -> None:
    resp = await client.post(
        "/v1/auth/register",
        json={"email": "veli1@example.com", "password": "gizli-parola-123", "role": "guardian"},
    )
    assert resp.status_code == 201

    login = await client.post(
        "/v1/auth/login", json={"email": "veli1@example.com", "password": "gizli-parola-123"}
    )
    assert login.status_code == 200
    body = login.json()
    assert body["access_token"] and body["refresh_token"]

    # refresh rotasyonu
    refresh = await client.post("/v1/auth/refresh", json={"refresh_token": body["refresh_token"]})
    assert refresh.status_code == 200
    rotated = refresh.json()
    assert rotated["refresh_token"] != body["refresh_token"]

    # eski refresh artik gecersiz
    again = await client.post("/v1/auth/refresh", json={"refresh_token": body["refresh_token"]})
    assert again.status_code == 401

    # logout yeni refresh'i iptal eder
    logout = await client.post("/v1/auth/logout", json={"refresh_token": rotated["refresh_token"]})
    assert logout.status_code == 204
    after_logout = await client.post(
        "/v1/auth/refresh", json={"refresh_token": rotated["refresh_token"]}
    )
    assert after_logout.status_code == 401


async def test_guardian_cannot_access_other_child(client: httpx.AsyncClient) -> None:
    h1 = await _register_guardian(client, "veli-a@example.com")
    h2 = await _register_guardian(client, "veli-b@example.com")
    created = await client.post(
        "/v1/children",
        json={"nickname": "Ali", "birth_year": 2015, "grade": 6, "purposes": ["service"]},
        headers=h1,
    )
    assert created.status_code == 201
    child_id = created.json()["id"]

    other = await client.get(f"/v1/children/{child_id}", headers=h2)
    assert other.status_code == 404


async def test_child_token_requires_service_consent(client: httpx.AsyncClient) -> None:
    h = await _register_guardian(client, "veli-c@example.com")
    created = await client.post(
        "/v1/children",
        json={"nickname": "Ayşe", "birth_year": 2013, "grade": 8, "purposes": ["service"]},
        headers=h,
    )
    assert created.status_code == 201
    child_id = created.json()["id"]

    pairing = await client.post(f"/v1/children/{child_id}/device-pairing", headers=h)
    assert pairing.status_code == 200
    code = pairing.json()["code"]

    paired = await client.post("/v1/auth/child-pair", json={"child_id": child_id, "code": code})
    assert paired.status_code == 200
    child_token = paired.json()["access_token"]

    me = await client.get("/v1/children/me", headers={"Authorization": f"Bearer {child_token}"})
    assert me.status_code == 200
    assert me.json()["id"] == child_id

    # rızayı geri çek → çocuk tokenı geçersiz
    revoke = await client.post(
        f"/v1/children/{child_id}/consents",
        json={"purposes": ["service"], "grant": False},
        headers=h,
    )
    assert revoke.status_code == 204

    me_after = await client.get(
        "/v1/children/me", headers={"Authorization": f"Bearer {child_token}"}
    )
    assert me_after.status_code == 403

    pairing_after = await client.post(f"/v1/children/{child_id}/device-pairing", headers=h)
    assert pairing_after.status_code == 403


async def test_pairing_max_attempts(client: httpx.AsyncClient) -> None:
    h = await _register_guardian(client, "veli-d@example.com")
    created = await client.post(
        "/v1/children",
        json={"nickname": "Can", "birth_year": 2012, "grade": 9, "purposes": ["service"]},
        headers=h,
    )
    child_id = created.json()["id"]
    pairing = await client.post(f"/v1/children/{child_id}/device-pairing", headers=h)
    assert pairing.status_code == 200
    code = pairing.json()["code"]
    wrong = "999999" if code != "999999" else "000000"

    for _ in range(5):
        resp = await client.post("/v1/auth/child-pair", json={"child_id": child_id, "code": wrong})
        assert resp.status_code == 400

    # 5 deneme doldu → doğru kod bile reddedilir
    locked = await client.post("/v1/auth/child-pair", json={"child_id": child_id, "code": code})
    assert locked.status_code == 400
