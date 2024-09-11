class Prompt:
    ANSWER_PROMPT = """Based on the following context and the question, provide a comprehensive  and only related content answer to the question:

                Context: {combined_input}

                Question: {subquery}
                """

    DECOMPOSE_PROMPT = """
                Task: Decompose the following user request websearchquery into maximum of {num_queries} distinct subwebsearchquery that together will comprehensively answer the main websearchquery.
                Note: there is no restriction to get the exact {num_queries} subwebsearchquery it can be less than max if it covers our user whole point of view.
                Main websearchquery: "{websearchquery}"

                Instructions:
                1. Each subwebsearchquery should focus on a specific aspect of the main websearchquery.
                2. Ensure the websearchquery are clear, concise, and directly related to the main subwebsearchquery.
                3. The subwebsearchquery should cover different aspects and not be repetitive.
                """

    NODE_DEPENDENCY_PROMPT = """Does the answer to '{first}' depend on the answer to '{second}'? 
                        Answer with 'Yes' or 'No'."""

    RELEVANT_INFO_PROMPT = """
            Based on the following information:

            Subquery: {subquery}
            Web search result: {web_result}
            Context from child queries: {child_context}

            Extract and summarize the most relevant information that answers the subquery and would be useful for parent queries. 
            Ensure the summary is concise but comprehensive.
            """

    COMPREHENSIVE_ANSWER_PROMPT = """
            Based on the following context, provide a comprehensive answer to the original query:

            Context:
            {final_context}

            Original Query: {query}

            Please synthesize the information from all subqueries to give a complete and coherent answer.
            """
