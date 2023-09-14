words = []
with open("/usr/share/dict/words", "r") as f:
    for word in f:
        words.append(word.strip().lower())

print(words)
