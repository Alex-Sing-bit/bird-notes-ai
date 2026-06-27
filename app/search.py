from flask import current_app

import config

def find_bird(note):
    request = f"{config.QUERY_PREFIX}{note}"

    result = current_app.config['CHROMA_COLLECTION'].query(query_texts=[request], n_results=config.DEFAULT_SEARCH_RESULTS)
    print(result)

    return dict(result)
