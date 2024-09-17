import json

from pyopengenai import MultiAgentQueryOrchestrator, RealTimeGoogleSearchProvider

if __name__ == '__main__':
    processor = MultiAgentQueryOrchestrator(
        response_level="medium",
        device="GPU"
    )
    query = "language models that better other thatn qwen2 0.5b model , i want similar good and best latest model"
    result = processor.process_query(query)
    with open("/home/ntlpt59/Documents/DATA_LAKE/Dumps/MultiAgentQueryOrchestrator/result.json", "w") as f:
        json.dump(processor.results, f, indent=2)