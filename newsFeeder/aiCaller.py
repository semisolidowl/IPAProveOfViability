import ollama


def getAiSummary(message):
    print('in ai gen')
    client = ollama.Client(
        host='https://ollama-deployment.onwireway.online',
    )
    response = client.generate(
        model='llama3.2',
        system='you are going to receive a news article, you will summarize this article in 2-4 sentences, you will not return anything besides the summary, only information found in the article should be used!',
        prompt=message
    )
    print("new gen: ",response['response'])
    return response['response']


def getAiQualityFilter(message):
    print('in ai filter')
    client = ollama.Client(
        host='https://ollama-deployment.onwireway.online',
    )
    response = client.chat(
        options={
            "temperature":0.25,
            "top K":2
            },
        model='llama3.2',
        messages=[{
            "role": "user",
            "content": "Please assess if the content provided by the user is IT-related and business appropriate. Exclude any gaming or streaming content. Only allow articles that provide news, information, or insights about the IT industry. If the content fulfills any other requirements (such as being a review or advertisement), do not consider it eligible for approval. If the content does not meet any of these criteria, respond 'false'. If it meets all the criteria, respond with a clear 'true' without additional context."
        },
            {
            "role": "assistant",
            "content": "{\"message\": I'm ready to assess. Please go ahead and provide the content. I will respond with \"true\" if it meets the criteria,\"false\" otherwise.}"
        },
            {
            "role": "user",
            "content": message
        }]
    )
    print("filter: ",response['message']['content'])
    return response['message']['content']


def getAiglossary(message):
    client = ollama.Client(
        host='https://ollama-deployment.onwireway.online',
    )
    response = client.chat(
        model='llama3.2',
        messages=[{
            "role": "system",
            "content": "You are going to write a glossary with the size of up to 10 uncommon words. Your answers are JSON only."
        },
            {
            "role": "assistant",
            "content": "{\"message\": \"Understood. I will output my answers in JSON format.\" }"
        },
            {
            "role": "user",
            "content": message
        }]
    )
    return response['message']['content']
