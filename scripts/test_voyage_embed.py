from dotenv import load_dotenv
import voyageai

load_dotenv()

client = voyageai.Client()

result = client.embed(["Hello World"], model = "voyage-3", input_type= "document")
print(result.embeddings)
print(len(result.embeddings[0]))