from data.index_mapping import movie_review_mapping
from src.elasticsearch_client import ElasticsearchClient
from src.faker_class import FakerWrapper
from src.logger import Logger
from src.search_menu import SearchMenu

logger = Logger(__name__)


def choose_index(es):
    """
    Let user choose an existing index
    or create a new one.
    """

    indexes = es.get_indexes()

    if indexes:
        print("\n📋 Existing indexes:")
        for index in indexes:
            print(f"   - {index}")
    else:
        print("\n📭 No existing indexes found.")

    # ✅ اعتبارسنجی y/n
    while True:
        choice = input("\n Create new index? (y/n): ").strip().lower()

        if choice in ['y', 'n']:
            break
        else:
            print("❌ Invalid input! Please enter 'y' or 'n' only.")

    if choice == "y":
        # ✅ اعتبارسنجی نام ایندکس (نباید خالی باشه)
        while True:
            index_name = input("📝 Index name: ").strip()
            if index_name:
                break
            print("❌ Index name cannot be empty!")

        es.create_index(
            index_name,
            movie_review_mapping
        )

        # ✅ اعتبارسنجی تعداد document
        while True:
            try:
                document_count = int(
                    input("🔢 Number of fake documents: ")
                )
                if document_count > 0:
                    break
                else:
                    print("❌ Number must be greater than 0!")
            except ValueError:
                print("❌ Please enter a valid number!")

        return index_name, document_count

    else:
        # ✅ اعتبارسنجی انتخاب ایندکس موجود
        while True:
            index_name = input("📝 Enter existing index name: ").strip()
            if index_name:
                break
            print("❌ Index name cannot be empty!")

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
