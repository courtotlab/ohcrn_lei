import re
import pytest
from enum import Enum

# Import the functions from your module.
from ohcrn_lei.regex_utils import (
    get_coding_changes,
    get_genomic_changes,
    get_protein_changes,
    get_variant_ids,
    get_chromosomes,
    get_matches,
)

# Helper tests for get_matches can be conducted indirectly via the functions below.
# For the purposes of these tests we provide sample texts where changes are embedded.

# --- get_coding_changes tests ---

@pytest.mark.parametrize("text,expected_pattern", [
    # Simple substitution example, e.g., c.76A>T
    ("Mutation occurred at c.76A>T in this sample.", r"c\.76A>T"),
    # Silent mutation with "=," e.g., c.76=
    ("The result was c.76=.", r"c\.76="),
    # delins mutation example, e.g., c.123_124delinsAT
    ("Observed c.123_124delinsAT in the sample", r"c\.123_124delinsAT"),
    # del mutation example, e.g., c.345delC
    ("Detected c.345delC.", r"c\.345delC"),
    # ins mutation e.g., c.789_790insATG
    ("Found c.789_790insATG mutation", r"c\.789_790insATG"),
    # inversion e.g., c.111_113inv
    ("Note c.111_113inv now", r"c\.111_113inv"),
    # duplication mutation e.g., c.234dupG
    ("Examine c.234dupG in the DNA", r"c\.234dupG"),
])
def test_get_coding_changes(text, expected_pattern):
    results = get_coding_changes(text)
    # Check at least one match matches expected regex
    matches = [m for m in results if re.fullmatch(expected_pattern, m)]
    assert matches, f"No matches found for expected pattern in results: {results}"

def test_get_coding_changes_no_match():
    # A text without any valid coding change.
    text = "This text does not contain any coding change."
    results = get_coding_changes(text)
    assert results == []


# --- get_genomic_changes tests ---

@pytest.mark.parametrize("text,expected_pattern", [
    # Simple genomic change: g.12345A>T
    ("The genomic variant g.12345A>T was observed.", r"g\.12345A>T"),
    # Deletion, duplication, etc: g.1000_1005del
    ("The variant is g.1000_1005del", r"g\.1000_1005del"),
])
def test_get_genomic_changes(text, expected_pattern):
    results = get_genomic_changes(text)
    matches = [m for m in results if re.fullmatch(expected_pattern, m)]
    assert matches, f"Expected match for pattern {expected_pattern}, got: {results}"

def test_get_genomic_changes_no_match():
    text = "No genomic change information available here."
    results = get_genomic_changes(text)
    assert results == []


# --- get_protein_changes tests ---

@pytest.mark.parametrize("text,expected_substring", [
    # Typical protein change: p.Val600Glu or without the leading "p."
    ("The protein mutation p.Val600Glu was detected.", "Val600Glu"),
    ("Protein variant Arg117His is noted.", "Arg117His"),
    # Combined variant (multiple separated by semicolons)
    ("p.(Met1Trp;Arg97Ser)", "Met1Trp"),
])
def test_get_protein_changes(text, expected_substring):
    results = get_protein_changes(text)
    # We'll test that at least one of the returned strings has the expected substring.
    found = any(expected_substring in r for r in results)
    assert found, f"Expected substring '{expected_substring}' not found in {results}"

def test_get_protein_changes_no_match():
    text = "No valid protein variant info here."
    results = get_protein_changes(text)
    assert results == []


# --- get_variant_ids tests ---

@pytest.mark.parametrize("text,expected_values", [
    # Test OMIM numbers.
    ("We found OMIM: 123456 in the patient.", ["OMIM: 123456"]),
    # Test ClinVar IDs.
    ("We found Clinvar:RCV000012345 in the patient.", ["RCV000012345"]),
    # Test dbSNP rs numbers.
    ("We found dbSNP:rs7891011 in the patient.", ["rs7891011"]),
    # Test COSMIC.
    ("We found COSMIC:COSM123456 in the patient.", ["COSMIC:COSM123456"]),
    # Test clingene.
    ("We found clingene:CA987654 in the patient.", ["clingene:CA987654"]),
    # Test uniprot.
    ("We found uniprot:.var:112233 in the patient.", ["uniprot:.var:112233"]),
    # Test with multiple matches in one string.
    ("We found OMIM:123456 and dbSNP:rs7891011 in the patient.", ["OMIM:123456", "rs7891011"]),
])
def test_get_variant_ids(text, expected_values):
    results = get_variant_ids(text)
    # Since the order is unimportant, check that each expected value is in the results.
    for expected in expected_values:
        assert expected in results

def test_get_variant_ids_no_match():
    text = "There is no valid variant id here."
    results = get_variant_ids(text)
    assert results == []


# --- get_chromosomes tests ---

@pytest.mark.parametrize("text,expected", [
    # Exact match for chromosome formats (entire string must match the pattern)
    ("Chr1", ["1"]),
    ("Chr10", ["10"]),
    ("ChrX", ["X"]),
    ("ChrY", ["Y"]),
])
def test_get_chromosomes_valid(text, expected):
    results = get_chromosomes(text)
    assert results == expected

@pytest.mark.parametrize("text", [
    # Strings that do not match the pattern, extra characters or missing prefix.
    "chr1",      # lowercase 'c'
    ("Chr23"),   # invalid: 23 is out of range
    "Chromosome1", 
    "1", 
    "this is Chr1",  # additional text
])
def test_get_chromosomes_no_match(text):
    results = get_chromosomes(text)
    assert results == []
