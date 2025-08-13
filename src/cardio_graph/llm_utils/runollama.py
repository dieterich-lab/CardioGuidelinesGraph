from ollama import Client

llama4 = 'http://10.250.135.153:11430'


client = Client(
  host=llama4,
  headers={'x-some-header': 'some-value'}
)
response = client.chat(model='qwen3:32b', options={'temperature': 0.0 } ,messages=[
  {
    'role': 'user',
    'content': 'give me the first 1o fibanocci numbers'
  },
])

print(response['message']['content'])