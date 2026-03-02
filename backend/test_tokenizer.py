from similarity.tokenizer import tokenize
from similarity.kgram import generate_kgrams
from similarity.fingerprint import generate_fingerprints

text = "This is a simple plagiarism detection test example"
tokens = tokenize(text)

kgrams = generate_kgrams(tokens, k=3)
fingerprints = generate_fingerprints(kgrams)

print("K-grams:")
print(kgrams)

print("\nFingerprints:")
print(fingerprints)