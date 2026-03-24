def test_create_project(client):
    response = client.post("/api/projects", json={"name": "New Coaster"})
    assert response.status_code == 200
    assert response.json()["metadata"]["name"] == "New Coaster"


def test_get_project(client):
    create_resp = client.post("/api/projects", json={"name": "Test"})
    project_id = create_resp.json()["id"]
    response = client.get(f"/api/projects/{project_id}")
    assert response.status_code == 200


def test_update_project(client):
    create_resp = client.post("/api/projects", json={"name": "Original"})
    project_id = create_resp.json()["id"]
    response = client.put(f"/api/projects/{project_id}", json={"metadata": {"name": "Updated"}})
    assert response.json()["metadata"]["name"] == "Updated"


def test_delete_project(client):
    create_resp = client.post("/api/projects", json={"name": "Delete"})
    project_id = create_resp.json()["id"]
    client.delete(f"/api/projects/{project_id}")
    response = client.get(f"/api/projects/{project_id}")
    assert response.status_code == 404


def test_list_projects(client):
    client.post("/api/projects", json={"name": "A"})
    client.post("/api/projects", json={"name": "B"})
    response = client.get("/api/projects")
    assert len(response.json()) >= 2