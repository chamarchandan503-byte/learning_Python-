
from openai import OpenAI

client = OpenAI()

def ask_ai(question):
    try:
        response = client.responses.create(
            model="gpt-5",
            input=question
        )

        return response.output_text

    except Exception as e:
        return f"AI Error: {e}"


# Test
answer = ask_ai("Hello, aap kaise hain?")
print(answer)
