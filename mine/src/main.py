from agent.agent import Agent
from dotenv import load_dotenv

load_dotenv(override=True)


def main():
    agent = Agent(system_message="You are a helpful assistant.")
    while True:
        user_message = input("User: ")
        if user_message.lower() in ["exit", "quit"]:
            print("Exiting the conversation.")
            break
        response = agent.run_conversation(user_message)
        print(f"Assistant: {response}")

    print("\nConversation History:")
    for message in agent.conversation_history:
        role = message["role"]
        content = message["content"]
        print(f"{role.capitalize()}: {content}")


if __name__ == "__main__":
    main()
