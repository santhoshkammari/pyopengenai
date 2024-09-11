from opengenai.researcher_ai import MultiAgentQueryOrchestrator

if __name__ == '__main__':
    processor = MultiAgentQueryOrchestrator(
            response_level="low",
            device="GPU"
        )
    query = "when is pawan kalyan new movie OG release date?"
    result = processor.process_query(query)
    # print(processor.results)
    # results  = {'subqueries': ['when is pawan kalyan new movie release date', "what is the genre of pawan kalyan's new movie", "where can i watch pawan kalyan's new movie"], 'subquery_results': {2: {'web_result': "To answer your question, I would need more specific information about the Pawan Kalyan's new movie. Please provide details such as the title of the movie or any other relevant context to assist you better.", 'relevant_info': "Based on the given information, there is no specific Pawan Kalyan's new movie mentioned in the web search result. Please provide more details or context about the movie to assist me better."}, 1: {'web_result': "The genre of Pawan Kalyan's new movie is not explicitly mentioned in the provided context. The context only mentions his filmography and awards, but does not provide any information about the specific genre of a new movie he may be working on.", 'relevant_info': "The context provided does not contain any information about Pawan Kalyan's new movie genre. The only mention of his filmography and awards is in the first sentence, which states he has won several awards. Therefore, there is no relevant information to answer the subquery."}, 0: {'web_result': 'The answer to your question is: The gangster drama film starring Pawan Kalyan and Emraan Hashmi will be released in September this year.', 'relevant_info': 'The answer to your question is: The gangster drama film starring Pawan Kalyan and Emraan Hashmi will be released in September this year.'}}, 'final_answer': 'The Gangster Drama Film Starring Pawan Kalyan And Emraan Hashmi Will Be Released In September This Year.'}
