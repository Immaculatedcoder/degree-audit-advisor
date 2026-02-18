from advisor_engine import create_advisor, get_advisor_response

llm, vector_store, system_prompt = create_advisor()

test_questions = [
    "What are the core courses required for BS Math?",
    "Is MATH 401 offered in the Fall?"
]


for i, question in enumerate(test_questions, 1):
    print(f"\n{'='*60}")
    print(f"💬 Test {i}: {question}")
    print(f"{'='*60}")

    conversation = [{"role": "user", "content": question}]
    response = get_advisor_response(llm, vector_store, system_prompt, conversation)

    print(f"\n🎓 Response:\n{response}")
    
    input("\n⏎ Press Enter for next question...")