"""Validation endpoint tests."""
import pytest


def test_validate_protein_identifiers_success(client):
    """Test validating protein identifiers."""
    response = client.post(
        "/api/validate/protein",
        json={
            "uniprot_accession_number": "P12345",
            "uniprot_entry_name": "TEST_HUMAN",
            "protein_name": "Test Protein"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True


def test_validate_protein_identifiers_empty(client):
    """Test validating empty protein identifiers."""
    response = client.post(
        "/api/validate/protein",
        json={}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    # Should have warnings about missing fields
    assert len(data["warnings"]) > 0


def test_validate_state_success(client):
    """Test validating a valid state."""
    state_data = {
        "id": "test-state-1",
        "name": "Test State",
        "description": "A test state",
        "protein_state": {
            "sequence": "MLIKLLTKVFGSRN",  # 14 amino acids
            "n_term": 1,
            "c_term": 14,
            "oligomeric_state": 2
        },
        "peptides": [
            {
                "id": "peptide-1",
                "data_file_id": "file-1",
                "data_format": "DynamX_v3_state",
                "deuteration_type": "partially_deuterated",
                "filters": {},
                "chain": ["A"]
            }
        ]
    }

    response = client.post("/api/validate/state", json=state_data)

    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert len(data["errors"]) == 0


def test_validate_state_sequence_length_mismatch(client):
    """Test validation fails when sequence length doesn't match n_term/c_term."""
    state_data = {
        "id": "test-state-1",
        "name": "Test State",
        "description": "A test state",
        "protein_state": {
            "sequence": "MLIKLLT",  # 7 amino acids
            "n_term": 1,
            "c_term": 14,  # But c_term - n_term + 1 = 14
            "oligomeric_state": 2
        },
        "peptides": []
    }

    response = client.post("/api/validate/state", json=state_data)

    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert len(data["errors"]) > 0
    assert "Sequence length" in data["errors"][0]


def test_validate_state_no_peptides(client):
    """Test validation warns when no peptides are defined."""
    state_data = {
        "id": "test-state-1",
        "name": "Test State",
        "description": "A test state",
        "protein_state": {
            "sequence": "MLIKLLTKVFGSRN",
            "n_term": 1,
            "c_term": 14,
            "oligomeric_state": 2
        },
        "peptides": []
    }

    response = client.post("/api/validate/state", json=state_data)

    assert response.status_code == 200
    data = response.json()
    # Should still be valid but have warnings
    assert len(data["warnings"]) > 0
    assert any("peptides" in w.lower() for w in data["warnings"])


def test_validate_metadata_success(client):
    """Test validating metadata with all required fields."""
    metadata = {
        "authors": [
            {
                "name": "John Doe",
                "orcid": "0000-0001-2345-6789",
                "affiliation": "Test University"
            }
        ],
        "license": "CC BY 4.0"
    }

    response = client.post("/api/validate/metadata", json=metadata)

    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True


def test_validate_metadata_missing_license(client):
    """Test validation fails when license is missing."""
    metadata = {
        "authors": [
            {"name": "John Doe"}
        ],
        "license": ""  # Empty license
    }

    response = client.post("/api/validate/metadata", json=metadata)

    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert any("license" in e.lower() for e in data["errors"])


def test_validate_metadata_no_authors(client):
    """Test validation fails when no authors are provided."""
    metadata = {
        "authors": [],
        "license": "CC0"
    }

    response = client.post("/api/validate/metadata", json=metadata)

    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert any("author" in e.lower() for e in data["errors"])


def test_validate_metadata_invalid_orcid(client):
    """Test validation fails with invalid ORCID format."""
    metadata = {
        "authors": [
            {
                "name": "John Doe",
                "orcid": "invalid-orcid"
            }
        ],
        "license": "CC0"
    }

    response = client.post("/api/validate/metadata", json=metadata)

    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert any("orcid" in e.lower() for e in data["errors"])


def test_validate_metadata_invalid_doi(client):
    """Test validation fails with invalid DOI format."""
    metadata = {
        "authors": [{"name": "John Doe"}],
        "license": "CC0",
        "publication": {
            "doi": "invalid-doi"
        }
    }

    response = client.post("/api/validate/metadata", json=metadata)

    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert any("doi" in e.lower() for e in data["errors"])


def test_validate_metadata_valid_doi(client):
    """Test validation succeeds with valid DOI format."""
    metadata = {
        "authors": [{"name": "John Doe"}],
        "license": "CC0",
        "publication": {
            "doi": "10.1234/example.2024"
        }
    }

    response = client.post("/api/validate/metadata", json=metadata)

    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
