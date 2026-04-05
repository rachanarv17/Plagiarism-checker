from plagiarism_checker import process_document
import os

# Create a dummy file with Wikipedia content
test_file = '/tmp/test_plagiarism.txt'
with open(test_file, 'w', encoding='utf-8') as f:
    f.write('Python is a high-level, general-purpose programming language. Its design philosophy emphasizes code readability with the use of significant indentation.')

results = process_document(test_file)
print("RESULTS:", results)
