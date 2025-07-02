from transformers import pipeline

generator = pipeline("text2text-generation", model="tiiuae/falcon-rw-1b")

def obtener_respuesta(prompt: str) -> str:
    entrada = f"Responde como un agente de eCommerce: {prompt}"
    resultado = generator(entrada, max_new_tokens=60)
    return resultado[0]["generated_text"].strip()
