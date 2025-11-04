"""File upload and management tests."""
import pytest


def test_upload_csv_file(client, session_id, sample_csv_file):
    """Test uploading a CSV data file."""
    filename, content, content_type = sample_csv_file

    response = client.post(
        "/api/files/upload",
        data={
            "session_id": session_id,
            "file_type": "data"
        },
        files={"file": (filename, content, content_type)}
    )

    assert response.status_code == 200
    data = response.json()

    # Check response structure
    assert "id" in data
    assert data["filename"] == filename
    assert data["size"] == len(content)
    assert data["file_type"] == "data"


def test_upload_pdb_file(client, session_id, sample_pdb_file):
    """Test uploading a PDB structure file."""
    filename, content, content_type = sample_pdb_file

    response = client.post(
        "/api/files/upload",
        data={
            "session_id": session_id,
            "file_type": "structure"
        },
        files={"file": (filename, content, content_type)}
    )

    assert response.status_code == 200
    data = response.json()

    # Check response structure
    assert "id" in data
    assert data["filename"] == filename
    assert data["size"] == len(content)
    assert data["file_type"] == "structure"


def test_upload_multiple_files(client, session_id, sample_csv_file):
    """Test uploading multiple files to the same session."""
    filename, content, content_type = sample_csv_file

    # Upload first file
    response1 = client.post(
        "/api/files/upload",
        data={"session_id": session_id, "file_type": "data"},
        files={"file": (filename, content, content_type)}
    )
    assert response1.status_code == 200
    file1_id = response1.json()["id"]

    # Upload second file
    response2 = client.post(
        "/api/files/upload",
        data={"session_id": session_id, "file_type": "data"},
        files={"file": ("another_file.csv", content, content_type)}
    )
    assert response2.status_code == 200
    file2_id = response2.json()["id"]

    # File IDs should be different
    assert file1_id != file2_id


def test_list_files(client, session_id, sample_csv_file):
    """Test listing uploaded files."""
    filename, content, content_type = sample_csv_file

    # Upload a file
    upload_response = client.post(
        "/api/files/upload",
        data={"session_id": session_id, "file_type": "data"},
        files={"file": (filename, content, content_type)}
    )
    assert upload_response.status_code == 200

    # List files
    list_response = client.get(
        "/api/files/list",
        params={"session_id": session_id}
    )
    assert list_response.status_code == 200

    data = list_response.json()
    assert "files" in data
    assert len(data["files"]) == 1
    assert data["files"][0]["filename"] == filename


def test_delete_file(client, session_id, sample_csv_file):
    """Test deleting an uploaded file."""
    filename, content, content_type = sample_csv_file

    # Upload a file
    upload_response = client.post(
        "/api/files/upload",
        data={"session_id": session_id, "file_type": "data"},
        files={"file": (filename, content, content_type)}
    )
    assert upload_response.status_code == 200
    file_id = upload_response.json()["id"]

    # Delete the file
    delete_response = client.delete(
        f"/api/files/{file_id}",
        params={"session_id": session_id}
    )
    assert delete_response.status_code == 200

    # Verify file is gone
    list_response = client.get(
        "/api/files/list",
        params={"session_id": session_id}
    )
    assert len(list_response.json()["files"]) == 0


def test_upload_without_session_id(client, sample_csv_file):
    """Test that upload without session_id fails appropriately."""
    filename, content, content_type = sample_csv_file

    response = client.post(
        "/api/files/upload",
        data={"file_type": "data"},  # Missing session_id
        files={"file": (filename, content, content_type)}
    )

    # Should fail with 422 (validation error)
    assert response.status_code == 422


def test_delete_nonexistent_file(client, session_id):
    """Test deleting a file that doesn't exist."""
    response = client.delete(
        "/api/files/nonexistent-file-id",
        params={"session_id": session_id}
    )

    # Should return 404
    assert response.status_code == 404


def test_list_files_nonexistent_session(client):
    """Test listing files for a non-existent session."""
    response = client.get(
        "/api/files/list",
        params={"session_id": "nonexistent-session"}
    )

    # Should return 404
    assert response.status_code == 404
