from similarity.tokenizer import tokenize
from similarity.kgram import generate_kgrams

text = "This is a simple plagiarism detection test example"
tokens = tokenize(text)

kgrams = generate_kgrams(tokens, k=3)

print(kgrams)
# text = "Hello, HELLO! This is a test."
# tokens = tokenize(text)

# print(tokens)