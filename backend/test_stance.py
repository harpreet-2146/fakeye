from app.retriever.stance import detect_stance

tests = [
    (
        "Is Florida in India?",
        "Florida is a state located in the southeastern United States."
    ),
    (
        "Is Narendra Modi the Prime Minister of Africa?",
        "Narendra Modi is the Prime Minister of India."
    ),
    (
        "Are there 15 months in a year?",
        "There are 12 months in a year."
    ),
    (
        "Is the Earth flat?",
        "NASA and scientific consensus confirm the Earth is spherical."
    ),
    (
        "Is XYZ dead?",
        "XYZ appeared at a public event last week."
    ),
]

for claim, evidence in tests:
    result = detect_stance(claim, evidence)
    print("\nClaim:", claim)
    print("Evidence:", evidence)
    print("Result:", result.dict())
