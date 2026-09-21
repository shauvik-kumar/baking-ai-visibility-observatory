from google import genai

client = genai.Client()

interaction = client.interactions.create(
    model="gemini-3.6-flash",
    input="Why does an eggless cake sink after baking?"
)

print(interaction.output_text)