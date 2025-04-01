"""
OHCRN-LEI - LLM-based Extraction of Information
Copyright (C) 2025 Ontario Institute for Cancer Research

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import pytest

from ohcrn_lei.trieSearch import Trie


# A helper function to create a trie with sample words.
def create_sample_trie(words):
  trie = Trie()
  for word in words:
    trie.insert(word)
  return trie


def test_insert_and_search():
  # Insert multiple words and verify we can find them in a text.
  words = ["cat", "cater", "bat", "bath", "at"]
  trie = create_sample_trie(words)

  text = "the cat and the bat took a nap. the cater was busy."
  matches = trie.search_in_text(text)

  # Convert the result into a set for easier verification.
  result_set = set(matches)
  # Expected matches: for each occurrence of any inserted word.
  expected_words = []

  # Build expected matches by scanning the text in a simple way.
  # This is a naive construction of the expected result.
  for i in range(len(text)):
    for word in words:
      if text.startswith(word, i):
        expected_words.append((i, word))
  expected_set = set(expected_words)

  assert result_set == expected_set


def test_search_in_text_overlap():
  # Test scenarios where one word is a prefix for another.
  words = ["a", "ab", "abc"]
  trie = create_sample_trie(words)

  text = "abc ab a abc"
  matches = trie.search_in_text(text)

  # Check that all valid matches (including overlapping ones) are found.
  expected_matches = [
    (0, "a"),
    (0, "ab"),
    (0, "abc"),
    (4, "a"),
    (4, "ab"),
    (7, "a"),
    (9, "a"),
    (9, "ab"),
    (9, "abc"),
  ]
  assert set(matches) == set(expected_matches)


def test_serialization_and_deserialization():
  # Test that serializing and then deserializing produces an equivalent Trie.
  words = ["hello", "helium", "hero", "her"]
  trie = create_sample_trie(words)

  serialized = trie.serialize()
  new_trie = Trie.deserialize(serialized)

  # Test that search_in_text returns the same matches in a given text.
  text = "hello, did you see the hero and his helium balloons? her story was amazing."
  original_matches = set(trie.search_in_text(text))
  new_matches = set(new_trie.search_in_text(text))
  assert original_matches == new_matches


def test_empty_trie():
  # Create an empty trie and test that searching any text yields no matches.
  trie = Trie()
  text = "any text whatsoever"
  assert trie.search_in_text(text) == []

  # Test serialization & deserialization on an empty trie.
  serialized = trie.serialize()
  new_trie = Trie.deserialize(serialized)
  assert new_trie.search_in_text(text) == []


def test_deserialize_invalid_format():
  # Test that an invalid serialization string raises a ValueError.
  # e.g., missing a bracket.
  invalid_serialized = (
    "[1,a,[0]]"  # valid up to here, let's break it by removing closing ]
  )
  invalid_serialized = "[1,a,[0]"
  with pytest.raises(ValueError):
    Trie.deserialize(invalid_serialized)


def test_complex_serialization_structure():
  # Test with a more complex trie structure.
  words = ["apple", "app", "ape", "apricot", "bat", "ball", "bar", "base"]
  trie = create_sample_trie(words)
  serialized = trie.serialize()
  new_trie = Trie.deserialize(serialized)

  # Compare searches across a text.
  text = "I ate an apple and an ape while watching a bat fly near the ball."
  orig_matches = set(trie.search_in_text(text))
  new_matches = set(new_trie.search_in_text(text))
  assert orig_matches == new_matches


if __name__ == "__main__":
  pytest.main()
