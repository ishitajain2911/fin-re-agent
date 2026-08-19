from dotenv import load_dotenv
import os
import anthropic

load_dotenv()

client = anthropic.Anthropic()

response = client.messages.create(model='claude-sonnet-5', max_tokens= 100, messages=[{"role": "user", "content": " say hello in five words"}])
for block in response.content:
    if block.type == "text":
        print(block.text)