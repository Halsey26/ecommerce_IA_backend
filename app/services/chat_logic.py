from transformers import pipeline

# Carga del modelo liviano de Hugging Face
qa_pipeline = pipeline("text2text-generation", model="google/flan-t5-small")

def obtener_respuesta(prompt: str) -> str:
    respuesta = qa_pipeline(f"Responde como un agente de eCommerce: {prompt}", max_new_tokens=60)
    return respuesta[0]["generated_text"].strip()

