"""Vérification de la traçabilité : empreintes, journal, manifeste."""

import hashlib
import json
from datetime import datetime, timezone

import pytest

from excl2test.manifest import sha256_file
from excl2test.runner import STATUS_FAILED, STATUS_UNUSABLE, STATUS_VALID, check
from excl2test.sample_data import generate

NOW = datetime(2026, 10, 1, 12, 30, 0, tzinfo=timezone.utc)


@pytest.fixture
def files(tmp_path):
    return generate(tmp_path)


def _manifest(result):
    return json.loads(result.manifest_path.read_text(encoding="utf-8"))


# --- Empreinte SHA-256 -----------------------------------------------------

def test_sha256_matches_hashlib(tmp_path):
    f = tmp_path / "x.bin"
    f.write_bytes(b"abc")
    assert sha256_file(f) == hashlib.sha256(b"abc").hexdigest()


def test_sha256_changes_when_one_byte_changes(tmp_path):
    f = tmp_path / "x.bin"
    f.write_bytes(b"abc")
    before = sha256_file(f)
    f.write_bytes(b"abd")
    assert sha256_file(f) != before


# --- Journal et manifeste --------------------------------------------------

def test_valid_run_writes_log_and_manifest(files, tmp_path):
    valid_path, _ = files
    result = check(valid_path, tmp_path / "out", now=NOW)
    assert result.status == STATUS_VALID and result.exit_code == 0
    assert result.log_path.name == "cas_valides_20261001T123000Z.log"
    assert result.log_path.exists() and result.manifest_path.exists()
    text = result.log_path.read_text(encoding="utf-8")
    assert "SHA-256" in text and "VALIDE" in text


def test_manifest_content_for_failed_run(files, tmp_path):
    _, invalid_path = files
    result = check(invalid_path, tmp_path / "out", now=NOW)
    m = _manifest(result)
    assert result.status == STATUS_FAILED and result.exit_code == 1
    assert m["resultat"] == "ECHEC"
    assert m["nb_cas"] == 10 and m["nb_anomalies"] == 10 == len(m["anomalies"])
    assert m["fichier_entree"]["sha256"] == sha256_file(invalid_path)
    assert m["horodatage_utc"] == "2026-10-01T12:30:00Z"
    assert len(m["dictionnaire_sha256"]) == 64
    assert m["anomalies"][0]["code"] == "SIGNAL_UNKNOWN"
    assert m["anomalies"][0]["cellule"] == "C2"


def test_same_input_gives_identical_manifest(files, tmp_path):
    valid_path, _ = files
    m1 = _manifest(check(valid_path, tmp_path / "a", now=NOW))
    m2 = _manifest(check(valid_path, tmp_path / "b", now=NOW))
    assert m1 == m2


def test_unusable_file_is_still_traced(tmp_path):
    fake = tmp_path / "faux.xlsx"
    fake.write_text("pas un classeur")
    result = check(fake, tmp_path / "out", now=NOW)
    m = _manifest(result)
    assert result.status == STATUS_UNUSABLE and result.exit_code == 2
    assert m["resultat"] == "INEXPLOITABLE"
    assert m["fichier_entree"]["sha256"] == sha256_file(fake)
    assert m["erreur_structure"]
    assert m["dictionnaire_sha256"] is None


def test_missing_file_is_traced_without_hash(tmp_path):
    result = check(tmp_path / "absent.xlsx", tmp_path / "out", now=NOW)
    m = _manifest(result)
    assert result.status == STATUS_UNUSABLE
    assert m["fichier_entree"]["sha256"] is None
    assert m["fichier_entree"]["taille_octets"] is None
