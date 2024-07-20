# Testing breaking up transcripts that do not have chapters into sentence chunks. To fix an issue
from langchain_text_splitters import SpacyTextSplitter
# This is a long document we can split up.
with open(r'C:\Users\happy\Documents\Projects\obsidian-transcriber-service\tests\non_chunked_transcripts\lots-oh-words.md') as f:
    transcript = f.read()

# Strip leading whitespace (including \n\n) from the transcript
transcript = transcript.lstrip()

# Split the transcript into lines
lines = transcript.split('\n')

# Extract the first line as the title
title = lines[0]
# Join the remaining lines back into a single string
remaining_text = ''.join(lines[1:])
text_splitter = SpacyTextSplitter(chunk_size=10000)

texts = text_splitter.split_text(remaining_text)

# Join sentences into one chunk with a space between each sentence
formatted_text = '\n'.join(texts).replace('\n', ' ') + '\n\n'

# Save to a file.
# write to the non_chunked_transcripts folder
with open(r'C:\Users\happy\Documents\Projects\obsidian-transcriber-service\tests\non_chunked_transcripts\output.md', 'w') as f:
    f.write(formatted_text)
