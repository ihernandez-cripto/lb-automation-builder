from langchain_core.messages import HumanMessage
from graph import app

def run():
    print("=== LB Automation Builder (SmartVista) ===")
    prompt_user = input("Ingresa los requerimientos del Load Balancer:\n> ")
    
    input_state = {
        "messages": [HumanMessage(content=prompt_user)]
    }

    for event in app.stream(input_state):
        for node_name, state_update in event.items():
            print(f"\n[Ejecutando Nodo]: {node_name}")
            if "messages" in state_update and state_update["messages"]:
                print(f"Resultado parcial: {state_update['messages'][-1].content[:150]}...")

if __name__ == "__main__":
    run()