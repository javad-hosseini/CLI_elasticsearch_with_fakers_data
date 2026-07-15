# built-in
import functools

# third-side
from elasticsearch import Elasticsearch, helpers
from elasticsearch.exceptions import ConnectionError, NotFoundError, RequestError

# my-own
from src.configuration import Configuration
from src.logger import Logger

logger = Logger(__name__)


def handle_elasticsearch_errors(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):

        try:
            return func(*args, **kwargs)
        except NotFoundError as e:
            # Log a warning message for index or document not found errors
            logger.error(f"Index or document not found: {e}")
        except RequestError as e:
            # Log an error message for invalid request errors
            logger.error(f"Invalid request: {e}")
        except ConnectionError as e:
            # Connection error
            logger.error(f"Connection failed: {e}")
        except Exception as e:
            # more general error
            logger.error(f'General Error {str(e)}')

    return wrapper


class ElasticsearchClient:
    """
    Wrapper class around the official Elasticsearch Python client.

    This class hides the complexity of Elasticsearch operations and provides
    simple methods for:
    - Connecting to Elasticsearch
    - Creating indexes
    - Indexing documents
    - Searching documents
    - Updating and deleting documents
    - Bulk operations

    Instead of using the Elasticsearch client directly everywhere,
    the application communicates with Elasticsearch through this class.
    """

    def __init__(self):
        """
        Constructor method.

        When an ElasticsearchClient object is created:
        1. Load Elasticsearch configuration from config file
        2. Establish a connection with Elasticsearch cluster
        """

        # Load Elasticsearch configuration from app_config.yml
        # Example:
        # elasticsearch:
        #   host: localhost
        #   port: 9200
        #   username: elastic
        #   password: password
        self.config = Configuration().get_config('elasticsearch')

        # Create Elasticsearch connection and store the client instance
        # This object will be used for all Elasticsearch operations
        self.es = self.connect_to_elastic()

    @handle_elasticsearch_errors
    def connect_to_elastic(self):
        url = f"{self.config['host']}:{self.config['port']}"

        print("CONNECTING TO:", url)

        es = Elasticsearch(
            url,
            verify_certs=False
        )

        print("INFO:", es.info())

        print("PING:", es.ping())

        return es

    @handle_elasticsearch_errors
    def create_index(self, index_name: str, mapping: dict):
        """
        Creates a new Elasticsearch index.

        Args:
            index_name:
                Name of the index to create.

                Example:
                "movie_reviews"


            mapping:
                Elasticsearch index mapping.
                Defines the structure and datatype of fields.

                Example:
                {
                    "title": {
                        "type": "text"
                    },
                    "rating": {
                        "type": "float"
                    }
                }


        Elasticsearch API equivalent:

        PUT /movie_reviews
        {
          "mappings": {
            "properties": {
              ...
            }
          }
        }
        """

        # Create index and apply mapping definition
        self.es.indices.create(

            # Elasticsearch index name
            index=index_name,

            # Request body sent to Elasticsearch
            body={
                'mappings': {

                    # Defines fields and their data types
                    'properties': mapping
                }
            }
        )

        logger.info(f'Created index {index_name}')

        return True

    @handle_elasticsearch_errors
    def insert_one_document(self, index_name: str, body: dict, doc_id=None):
        """
        Inserts a single document into an Elasticsearch index.

        Args:
            index_name:
                Target Elasticsearch index.

            body:
                Document data that will be stored.

            doc_id:
                Optional custom document ID.

        Example:

        POST /movies/_doc
        {
            "title":"Inception",
            "rating":8.8
        }

        If doc_id is provided:

        PUT /movies/_doc/22
        """

        response = self.es.index(
            index=index_name,
            id=doc_id,
            body=body
        )

        logger.info(
            f"insert one document to {index_name} with body: {body}"
        )

        return True

    @handle_elasticsearch_errors
    def get_document(self, index_name: str, doc_id: int):
        """
        Retrieves a document from Elasticsearch using its ID.

        Elasticsearch API:

        GET /index_name/_doc/document_id


        Returns:
            Only the document source (_source),
            not the full Elasticsearch response.
        """

        response = self.es.get(
            index=index_name,
            id=doc_id
        )

        logger.info(
            f"Getting document from index: {index_name} with id: {doc_id}"
        )

        # Extract only the actual stored document
        #
        # Full response example:
        # {
        #   "_index":"movies",
        #   "_id":"22",
        #   "_source":{
        #       "title":"Batman"
        #   }
        # }
        #
        # We only return:
        # {
        #    "title":"Batman"
        # }
        return response['_source']

    @handle_elasticsearch_errors
    def update_document_by_id(
            self,
            index_name: str,
            doc_id: int,
            body: dict
    ):
        """
        Updates an existing document by ID.

        Elasticsearch API:

        POST /index/_update/id

        Example:
        Update only rating field:
        {
            "doc":{
                "rating":9
            }
        }
        """

        response = self.es.update(
            index=index_name,
            id=doc_id,
            body=body
        )

        logger.info(str(response))

        return True

    @handle_elasticsearch_errors
    def get_indexes(self):
        """
        Return all existing Elasticsearch indexes.
        """

        indexes = self.es.cat.indices(
            format="json"
        )

        return [
            index["index"]
            for index in indexes
        ]

    @handle_elasticsearch_errors
    def get_mapping(self, index_name: str):
        """
        Return mapping of an index.
        """

        mapping = self.es.indices.get_mapping(
            index=index_name
        )

        return mapping

    @handle_elasticsearch_errors
    def delete_index(self, index_name: str):

        if self.es.indices.exists(index=index_name):
            self.es.indices.delete(index=index_name)
            logger.info(
                f'Deleted index {index_name}'
            )
            return True

        logger.info(
            f'Index {index_name} does not exist'
        )

        return False

    @handle_elasticsearch_errors
    def delete_by_query(self, query: dict, index_name: str):
        """
        Deletes multiple documents that match a query.

        Example:

        Delete all documents where genre = Drama


        Elasticsearch API:

        POST /index/_delete_by_query
        """

        self.es.delete_by_query(

            # Target index
            index=index_name,

            # Query condition
            body={
                'query': query
            }
        )

        logger.info(
            f'Deleted documents from index {index_name} that match query {query}'
        )

    @handle_elasticsearch_errors
    def search(self, query: dict, index_name: str):
        """
        Searches documents inside an Elasticsearch index.

        Example query:

        Find Adventure movies with rating > 7


        Elasticsearch API:

        POST /index/_search
        """

        result = self.es.search(

            # Search inside this index
            index=index_name,

            # Search query
            body={
                'query': query
            }
        )

        logger.info(
            f'Search executed on index {index_name} with query {query}'
        )

        # Elasticsearch returns a large response.
        # We only return matched documents.

        # Response structure:
        #
        # hits:
        #   hits:
        #      [
        #        {
        #          "_source": {...}
        #        }
        #      ]

        return result['hits']['hits']

    @handle_elasticsearch_errors
    def count(self, index_name: str):
        """
        Counts documents inside an Elasticsearch index.

        Before counting, refresh is called.

        Why?

        Elasticsearch indexing is near real-time.
        Newly inserted documents may not be immediately searchable.

        Refresh makes recent changes visible.
        """

        # Make recent indexed documents searchable
        self.es.indices.refresh(
            index=index_name
        )

        # Count documents
        result = self.es.count(
            index=index_name
        )

        logger.info(
            f'Count executed on index {index_name}, '
            f'{result["count"]} documents!'
        )

        return result['count']

    @handle_elasticsearch_errors
    def scan_index(self, index_name: str):
        """
        Retrieves all documents from an index.

        Uses Elasticsearch scan helper.

        Why not normal search?

        Because search has size limitations.

        Scan uses scroll API internally and is suitable
        for processing large amounts of data.
        """

        response = helpers.scan(
            self.es,
            index=index_name
        )

        # Generator pattern:
        # Documents are returned one by one
        # instead of loading everything into memory.

        for doc in response:
            yield doc['_source']

    @handle_elasticsearch_errors
    def bulk_index_documents(
            self,
            index_name: str,
            documents: list
    ):
        """
        Inserts many documents into Elasticsearch using Bulk API.

        Normal insert:

        Document 1 -> HTTP request
        Document 2 -> HTTP request
        Document 3 -> HTTP request


        Bulk insert:

        1000 documents -> one HTTP request


        This is much faster for large datasets.
        """

        # Prepare documents in Elasticsearch bulk format
        actions = [

            {
                # Target index
                '_index': index_name,

                # Actual document data
                '_source': doc
            }

            for doc in documents
        ]

        # Send all documents at once
        response = helpers.bulk(
            self.es,
            actions
        )

        logger.info(
            f"Bulk insert {str(response)} documents "
            f"to {index_name} index"
        )

    @handle_elasticsearch_errors
    def search_and_save_results(self, query: dict, index_name: str, result_index_name: str = None):
        """
        Search documents and save results to a new index for Kibana visualization.

        Args:
            query: Elasticsearch query
            index_name: Source index to search in
            result_index_name: Name of the new index to save results (default: source_index_results)

        Returns:
            Number of documents saved
        """

        # اگه اسم ایندکس نتیجه رو ندادی، خودکار بساز
        if result_index_name is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result_index_name = f"{index_name}_results_{timestamp}"

        # اول search کن
        results = self.search(query=query, index_name=index_name)

        if not results:
            logger.warning("No results to save!")
            return 0

        # نتایج رو برای bulk insert آماده کن
        documents = [hit['_source'] for hit in results]

        # ایندکس جدید رو بساز (اگر وجود نداره)
        if not self.es.indices.exists(index=result_index_name):
            # از mapping ایندکس اصلی کپی می‌کنه
            original_mapping = self.es.indices.get_mapping(index=index_name)
            self.es.indices.create(
                index=result_index_name,
                body=original_mapping[index_name]
            )
            logger.info(f"Created new index: {result_index_name}")

        # نتایج رو bulk insert کن
        self.bulk_index_documents(result_index_name, documents)

        logger.info(f"Saved {len(documents)} documents to {result_index_name}")

        return result_index_name
