from pyopengenai.researcher_ai import RealTimeGoogleSearchProvider


searcher = RealTimeGoogleSearchProvider(search_provider="https://huggingface.co/chat/",
                                        animation=True)

print(searcher.perform_search("who is modi?"))
