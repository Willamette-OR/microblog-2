from flask import current_app


def add_to_index(index, model):
    """This function adds a given index along with a specified data model/table to the app's elasticsearch instance."""

    # return None if elasticsearch is not configured
    if not current_app.elasticsearch:
        return
    
    payload = {}
    for field in model.__searchable__:
        payload[field] = getattr(model, field)
    current_app.elasticsearch.index(index=index, id=model.id, body=payload)


def remove_from_index(index, model):
    """This function removes a given index from the app's elasticsearch instance."""

    # return None if elasticsearch is not configured
    if not current_app.elasticsearch:
        return 

    current_app.elasticsearch.delete(index=index, id=model.id)


def query_index(index, query, page, per_page):
    """This function queries a given index and a given query. It also takes a page and per_page number for pagination."""

    # return None if elasticsearch is not configured
    if not current_app.elasticsearch:
        return [], 0

    search = current_app.elasticsearch.search(index=index, body={'query': {'multi_match': {'query': query, 'fields': ['*']}},
                                                                 'from': (page - 1) * per_page, 'size': per_page})
    ids = [int(hit['_id']) for hit in search['hits']['hits']]
    return ids, search['hits']['total']['value']
