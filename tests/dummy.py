from pyopengenai.researcher_ai import RealTimeGoogleSearchProvider


searcher = RealTimeGoogleSearchProvider()

print(searcher.perform_search("who is modi?"))
