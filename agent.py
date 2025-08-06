from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import tool, AgentExecutor, create_tool_calling_agent
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv
import random
import json
load_dotenv()

# 1. Configuración mejorada del modelo
llm = ChatOllama(
    model="mistral",
    temperature=0.3,  # Reducido para mayor precisión
    num_ctx=4096,
    system="""Eres un camarero experto. Cuando un cliente pida un plato o bebida:
    1. Usa INMEDIATAMENTE la herramienta 'obtener_orden'
    2. Nunca expliques código o procesos técnicos
    3. Mantén respuestas naturales como un camarero real"""
)

def guardar_historial_en_json(historial, nombre_archivo="historial.json"):
    mensajes = []
    for mensaje in historial:
        if isinstance(mensaje, HumanMessage):
            mensajes.append({"role": "cliente", "content": mensaje.content})
        elif isinstance(mensaje, AIMessage):
            mensajes.append({"role": "camarero", "content": mensaje.content})
    
    with open(nombre_archivo, "w", encoding="utf-8") as f:
        json.dump(mensajes, f, ensure_ascii=False, indent=4)


# 2. Herramienta mejor definida
@tool
def obtener_orden(plato: str):
    """Registra una nueva orden de comida/bebida. Ejemplo de uso: obtener_orden('pizza margarita')"""
    data={"id":random.randint(1,10000), "pedido": plato}
    try:
        response = requests.post(  # Cambiado a POST para crear órdenes
            "http://127.0.0.1:8000/nueva_orden",
            json=data,
        )
        response.raise_for_status()
        return f"Orden registrada:"
    except Exception as e:
        return f"Error: No pude registrar la orden ({str(e)})"

tools = [obtener_orden]
llm = llm.bind_tools(tools)
# 3. Prompt más específico
prompt = ChatPromptTemplate.from_messages([
    ("system", "you're a helpful assistant"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

# 4. Agente con configuración optimizada
agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=3,
    early_stopping_method="generate"
)

# 5. Bucle de conversación con validación
history = []

print("¡Bienvenido al restaurante! ¿Qué desea ordenar?")
while True:
    try:
        user_input = input("\nCliente: ").strip()
        if user_input.lower() in ['salir', 'exit', 'adiós']:
            print("¡Gracias por su visita!")
            break

        response = agent_executor.invoke({
            "input": user_input,
            "chat_history": history

        })

        if response and 'output' in response:
            print(f"\nCamarero: {response['output']}")
            history.extend([
                HumanMessage(content=user_input),
                AIMessage(content=response['output'])
            ])
            guardar_historial_en_json(history)
        else:
            print("\nCamarero: Disculpe, no entendí. ¿Podría repetirlo?")

    except Exception as e:
        print(f"\nCamarero: ¡Ups! Problema técnico. {str(e)}")
        continue