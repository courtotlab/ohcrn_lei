class TrieNode:
  def __init__(self):
    # fields are a dictionary of child branches
    self.children = {}
    # and a flag to indicate whether a word terminates here
    self.is_end_of_word = False


class Trie:
  """
  A Trie structure stores words as a prefix-tree.
  It allows for fast string matching and is more compact than a full-on hash
  """

  def __init__(self):
    self.root = TrieNode()

  def insert(self, word):
    """Insert a word into the trie."""
    node = self.root
    for char in word:
      # if no branch for the letter exists, create one
      if char not in node.children:
        node.children[char] = TrieNode()
      # step into the branch
      node = node.children[char]
    node.is_end_of_word = True

  def search_in_text(self, text):
    """
    Given a Trie 'trie' holding a set of words and a long text document 'text',
    find all occurrences in the text that match any word in the Trie.
    The function returns a list of tuples: (start_index, matched_word).
    """
    matches = []
    n = len(text)

    # For each starting index in the text, try to follow the Trie
    for i in range(n):
      node = self.root
      j = i
      current_match = ""
      while j < n and text[j] in node.children:
        node = node.children[text[j]]
        current_match += text[j]
        # If we have found the end of a word, record the match
        if node.is_end_of_word:
          matches.append((i, current_match))
        j += 1
    return matches

  def serialize(self):
    """
    Serializes the entire trie structure into a string using bracket and comma delimiters.
    Format for a node is:
        [is_end, letter1, serialized(child1), letter2, serialized(child2), ...]
    is_end is 1 if the node marks the end of a word, 0 otherwise.
    """

    def serialize_node(node):
      # Start with the is_end flag.
      s = "[" + ("1" if node.is_end_of_word else "0")
      # Process children in sorted order for consistency
      for letter in sorted(node.children):
        s += "," + letter + "," + serialize_node(node.children[letter])
      s += "]"
      return s

    return serialize_node(self.root)

  @staticmethod
  def deserialize(s):
    """
    Deserializes the string 's' to reconstruct a Trie.
    Returns a new Trie object.
    """
    # Use a recursive parser that reads one node at a time.
    # The string format is assumed to be valid and in the format provided by serialize.
    index = 0

    def parse_node():
      nonlocal index
      # Expect the current character to be '['
      if s[index] != "[":
        raise ValueError("Expected '[' at position {}".format(index))
      index += 1  # skip '['

      # Read the is_end flag: we expect a single digit (0 or 1)
      if s[index] not in "01":
        raise ValueError("Expected '0' or '1' at position {}".format(index))
      node = TrieNode()
      node.is_end_of_word = s[index] == "1"
      index += 1

      # Now, while we see a comma, we parse letter and child node pairs.
      while index < len(s) and s[index] == ",":
        index += 1  # skip comma

        # Next should be a letter (assumed to be a non-comma, non-bracket character)
        letter = s[index]
        index += 1

        # Next character should be a comma before the child node.
        if s[index] != ",":
          raise ValueError("Expected ',' after letter at position {}".format(index))
        index += 1  # skip comma

        # Parse the child node (recursive call)
        child_node = parse_node()
        node.children[letter] = child_node

      # After processing children, we expect a closing bracket
      if index >= len(s) or s[index] != "]":
        raise ValueError("Expected ']' at position {}".format(index))
      index += 1  # skip ']'
      return node

    # Begin parsing from the root node.
    root_node = parse_node()
    trie = Trie()
    trie.root = root_node
    return trie
