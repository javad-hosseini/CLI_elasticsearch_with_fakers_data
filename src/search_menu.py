from src.logger import Logger


class SearchMenu:
    """
    Simple CLI menu for searching documents inside an Elasticsearch index.
    """

    def __init__(self, es_client, index_name):
        self.es = es_client
        self.index_name = index_name
        self.logger = Logger(__name__)

    def run(self):
        """
        Start the interactive search menu.
        """
        while True:

            self.show_menu()

            choice = input("Choose an option: ").strip()

            if choice == "1":
                self.search_by_field()

            elif choice == "2":
                self.show_available_fields()

            elif choice == "3":
                self.show_document_count()

            elif choice == "0":
                print("\nGoodbye!")
                break

            else:
                print("\nInvalid option.\n")

    def show_menu(self):
        """
        Print the main menu.
        """
        print("\n" + "=" * 40)
        print(f"Current Index : {self.index_name}")
        print("=" * 40)
        print("1. Search by field")
        print("2. Show available fields")
        print("3. Show document count")
        print("0. Exit")
        print("=" * 40)

    def show_available_fields(self):
        """
        Retrieve and display all fields from index mapping.
        """

        mapping = self.es.get_mapping(self.index_name)

        properties = mapping[self.index_name]["mappings"]["properties"]

        print("\nAvailable Fields:\n")

        for i, field in enumerate(properties.keys(), start=1):
            print(f"{i}. {field}")

    def search_by_field(self):
        """
        Search documents using a match query.
        """

        mapping = self.es.get_mapping(self.index_name)

        properties = mapping[self.index_name]["mappings"]["properties"]

        fields = list(properties.keys())

        print("\nAvailable Fields:\n")

        for i, field in enumerate(fields, start=1):
            print(f"{i}. {field}")

        try:
            choice = int(input("\nChoose field number: "))

            if choice < 1 or choice > len(fields):
                print("Invalid field.")
                return

        except ValueError:
            print("Please enter a valid number.")
            return

        selected_field = fields[choice - 1]

        value = input(f"Enter value for '{selected_field}': ")

        query = {
            "match": {
                selected_field: value
            }
        }

        results = self.es.search(
            index_name=self.index_name,
            query=query
        )

        self.print_results(results)

    def show_document_count(self):
        """
        Display total document count.
        """

        count = self.es.count(self.index_name)

        print(f"\nTotal Documents : {count}")

    def print_results(self, results):
        """
        Pretty print search results.
        """

        if not results:
            print("\nNo documents found.")
            return

        print(f"\nFound {len(results)} document(s).\n")

        for i, result in enumerate(results, start=1):

            print("-" * 50)
            print(f"Result #{i}")
            print("-" * 50)

            source = result["_source"]

            for key, value in source.items():
                print(f"{key:20}: {value}")

            print()