from src.faker_class import FakerWrapper
from src.elasticsearch_client import ElasticsearchClient
from src.logger import Logger
from data.index_mapping import movie_review_mapping
from src.search_menu import SearchMenu

logger = Logger(__name__)


def choose_index(es):
    """
    Let user choose an existing index
    or create a new one.
    """

    indexes = es.get_indexes()

    print("\nExisting indexes:")

    for index in indexes:
        print(f"- {index}")

    choice = input(
        "\nCreate new index? (y/n): "
    )

    if choice.lower() == "y":

        index_name = input(
            "Index name: "
        )

        es.create_index(
            index_name,
            movie_review_mapping
        )

        document_count = int(
            input(
                "Number of fake documents: "
            )
        )

        return index_name, document_count


    else:

        index_name = input(
            "Enter existing index name: "
        )

        return index_name, 0


def main():

    es = ElasticsearchClient()


    index_name, count = choose_index(es)


    if count > 0:

        faker = FakerWrapper()

        generator = faker.generate_data(
            mapping=faker.mapping,
            num_documents=count
        )


        documents = [
            next(generator)
            for _ in range(count)
        ]


        es.bulk_index_documents(
            index_name,
            documents
        )


    logger.info(
        f"Working with index: {index_name}"
    )

    menu = SearchMenu(
        es_client=es,
        index_name=index_name
    )

    menu.run()



if __name__ == "__main__":
    main()