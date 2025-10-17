def test_ingest_all(repo, all_dtos):
    result = repo.ingest_payload(payload=all_dtos)
    assert result

def test_get_user_data(repo, all_dtos, test_users):
    data = repo.get_user_data(user=test_users[0])
    assert data
