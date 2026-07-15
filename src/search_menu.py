import json

from src.logger import Logger


class SearchMenu:
    """
    Advanced CLI menu for searching documents inside an Elasticsearch index.
    Supports fuzzy search, range queries, and multi-field search.
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

            choice = input("\n🎬 Choose an option: ").strip()

            if choice == "1":
                self.search_by_field()

            elif choice == "2":
                self.fuzzy_search()

            elif choice == "3":
                self.search_by_range()

            elif choice == "4":
                self.search_by_date_range()

            elif choice == "5":
                self.multi_field_search()

            elif choice == "6":
                self.show_available_fields()

            elif choice == "7":
                self.show_document_count()

            elif choice == "8":
                self.show_sample_documents()

            elif choice == "9": 
                self.manage_result_indexes()

            elif choice == "0":
                print("\n👋 Goodbye!")
                break

            else:
                print("\n❌ Invalid option. Please try again.\n")

    def show_menu(self):
        """
        Print the main menu.
        """
        print("\n" + "=" * 50)
        print(f"🎥 CURRENT INDEX: {self.index_name}")
        print("=" * 50)
        print("1. 🔍 Basic Search (Match)")
        print("2. 🔍 Fuzzy Search (Typo-tolerant)")
        print("3. 📊 Range Search (Numeric fields)")
        print("4. 📅 Date Range Search")
        print("5. 🔍 Multi-Field Search")
        print("6. 📋 Show Available Fields")
        print("7. 📊 Show Document Count")
        print("8. 🎲 Show Sample Documents")
        print("9. 🗑️  Manage Result Indexes")
        print("0. 🚪 Exit")
        print("=" * 50)

    # ==================== HELPER METHODS ====================

    def show_available_fields(self):
        """
        Retrieve and display all fields from index mapping.
        """

        mapping = self.es.get_mapping(self.index_name)

        properties = mapping[self.index_name]["mappings"]["properties"]

        print("\n📋 Available Fields:\n")

        for i, field in enumerate(properties.keys(), start=1):
            field_type = properties[field].get('type', 'unknown')
            print(f"{i}. {field} ({field_type})")

    def get_fields_list(self):
        """Get list of available fields."""
        mapping = self.es.get_mapping(self.index_name)
        properties = mapping[self.index_name]["mappings"]["properties"]
        return list(properties.keys()), properties

    def select_field(self, fields, prompt="Choose field number: "):
        """Helper to select a field from list."""
        try:
            choice = int(input(f"\n{prompt}"))

            if choice < 1 or choice > len(fields):
                print("❌ Invalid field.")
                return None

        except ValueError:
            print("❌ Please enter a valid number.")
            return None

        return fields[choice - 1]

    def print_results(self, results):
        """
        Pretty print search results.
        """

        if not results:
            print("\n📭 No documents found.")
            return

        print(f"\n✅ Found {len(results)} document(s).\n")

        for i, result in enumerate(results, start=1):

            print("-" * 50)
            print(f"📄 Result #{i}")
            if '_score' in result:
                print(f"⭐ Score: {result['_score']:.2f}")
            print("-" * 50)

            source = result["_source"]

            for key, value in source.items():
                # Format key nicely
                formatted_key = key.replace('_', ' ').title()
                print(f"{formatted_key:20}: {value}")

            print()

    def print_query_dsl(self, query):
        """
        Print Elasticsearch Query DSL for Kibana Dev Tools.
        """
        full_query = {
            "query": query
        }

        print("\n" + "=" * 60)
        print("📋 ELASTICSEARCH QUERY DSL")
        print("=" * 60)
        print("💡 Copy this and paste in Kibana Dev Tools:\n")
        print(f"GET /{self.index_name}/_search")
        print(json.dumps(full_query, indent=2))
        print("\n" + "=" * 60)

    def execute_or_show_query(self, query):
        """
        Let user choose to see results, get Query DSL, or save for Kibana.
        """
        print("\n" + "-" * 50)
        print("📋 What would you like to do?")
        print("1. 📄 Show results here")
        print("2. 🔗 Get Query DSL (for Kibana Dev Tools)")
        print("3. 💾 Save results to new index (for Kibana Visualization)")
        print("4. 🔙 Cancel")
        print("-" * 50)

        while True:
            choice = input("\n🎯 Choose option (1/2/3/4): ").strip()

            if choice == "1":
                # Execute search and show results
                results = self.es.search(
                    index_name=self.index_name,
                    query=query
                )
                self.print_results(results)
                break

            elif choice == "2":
                # Show query DSL for Kibana
                self.print_query_dsl(query)
                break

            elif choice == "3":
                # Save results to new index for Kibana
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                result_index = f"{self.index_name}_results_{timestamp}"

                print(f"\n💾 Saving results to: {result_index}")

                result_index = self.es.search_and_save_results(
                    query=query,
                    index_name=self.index_name,
                    result_index_name=result_index
                )

                if result_index:
                    print("\n" + "=" * 60)
                    print("✅ SUCCESS! Results saved for Kibana")
                    print("=" * 60)
                    print(f"📊 Index name: {result_index}")
                    print("\n📋 Now in Kibana:")
                    print(f"   1. Go to Stack Management > Data Views")
                    print(f"   2. Create data view: {result_index}*")
                    print(f"   3. Go to Discover to see results")
                    print(f"   4. Create visualizations from there")
                    print("=" * 60)
                break

            elif choice == "4":
                print("🔙 Cancelled.")
                break

            else:
                print("❌ Invalid option! Please enter 1, 2, 3, or 4.")

    # ==================== SEARCH METHODS ====================

    def search_by_field(self):
        """
        Basic search using match query.
        """
        fields, properties = self.get_fields_list()

        print("\n📋 Available Fields:\n")

        for i, field in enumerate(fields, start=1):
            field_type = properties[field].get('type', 'unknown')
            print(f"{i}. {field} ({field_type})")

        selected_field = self.select_field(fields)

        if not selected_field:
            return

        value = input(f"\n🔍 Enter search value for '{selected_field}': ")

        query = {
            "match": {
                selected_field: value
            }
        }

        self.execute_or_show_query(query)

    def fuzzy_search(self):
        """
        Search with fuzzy logic (typo-tolerant).

        Example:
        - User types "actoin" -> finds "action"
        - User types "scifi" -> finds "science fiction"
        """
        fields, properties = self.get_fields_list()

        print("\n📋 Available Text Fields:\n")

        # Show only text-based fields suitable for fuzzy search
        text_fields = []
        for i, field in enumerate(fields, start=1):
            field_type = properties[field].get('type', 'unknown')
            if field_type in ['text', 'keyword']:
                text_fields.append(field)
                print(f"{len(text_fields)}. {field} ({field_type})")

        if not text_fields:
            print("❌ No text fields available for fuzzy search.")
            return

        try:
            choice = int(input(f"\n🔍 Choose field number for fuzzy search: "))

            if choice < 1 or choice > len(text_fields):
                print("❌ Invalid field.")
                return

        except ValueError:
            print("❌ Please enter a valid number.")
            return

        selected_field = text_fields[choice - 1]

        value = input(f"\n🔍 Enter search term (typos allowed): ")

        fuzziness = input("🎯 Fuzziness level (AUTO/1/2, default=AUTO): ").strip() or "AUTO"

        query = {
            "fuzzy": {
                selected_field: {
                    "value": value,
                    "fuzziness": fuzziness,
                    "max_expansions": 50
                }
            }
        }

        print(f"\n🔍 Prepared fuzzy search with fuzziness: {fuzziness}")

        self.execute_or_show_query(query)

    def search_by_range(self):
        """
        Search numeric fields by range (min, max).

        Examples:
        - Find movies with rating between 7 and 9
        - Find movies with duration between 90 and 120 minutes
        """
        fields, properties = self.get_fields_list()

        print("\n📊 Available Numeric Fields:\n")

        numeric_fields = []
        for i, field in enumerate(fields, start=1):
            field_type = properties[field].get('type', 'unknown')
            if field_type in ['float', 'integer', 'long', 'double']:
                numeric_fields.append(field)
                print(f"{len(numeric_fields)}. {field} ({field_type})")

        if not numeric_fields:
            print("❌ No numeric fields available for range search.")
            return

        try:
            choice = int(input(f"\n📊 Choose field number for range search: "))

            if choice < 1 or choice > len(numeric_fields):
                print("❌ Invalid field.")
                return

        except ValueError:
            print("❌ Please enter a valid number.")
            return

        selected_field = numeric_fields[choice - 1]

        try:
            min_value = float(input(f"\n📉 Enter MIN value for '{selected_field}': "))
            max_value = float(input(f"📈 Enter MAX value for '{selected_field}': "))
        except ValueError:
            print("❌ Please enter valid numbers.")
            return

        query = {
            "range": {
                selected_field: {
                    "gte": min_value,
                    "lte": max_value
                }
            }
        }

        print(f"\n🔍 Prepared range search: {selected_field} between {min_value} and {max_value}")

        self.execute_or_show_query(query)

    def search_by_date_range(self):
        """
        Search date fields by date range.

        Example:
        - Find movies released between 2015 and 2020
        """
        fields, properties = self.get_fields_list()

        print("\n📅 Available Date Fields:\n")

        date_fields = []
        for i, field in enumerate(fields, start=1):
            field_type = properties[field].get('type', 'unknown')
            if field_type in ['date']:
                date_fields.append(field)
                print(f"{len(date_fields)}. {field} ({field_type})")

        if not date_fields:
            print("❌ No date fields available.")
            return

        try:
            choice = int(input(f"\n📅 Choose field number: "))

            if choice < 1 or choice > len(date_fields):
                print("❌ Invalid field.")
                return

        except ValueError:
            print("❌ Please enter a valid number.")
            return

        selected_field = date_fields[choice - 1]

        print("\n📅 Enter dates in format: YYYY-MM-DD")
        print("   Examples: 2020-01-01")
        print("   or use 'now' for current date\n")

        start_date = input(f"📅 Start date: ").strip()
        end_date = input(f"📅 End date: ").strip()

        if not start_date or not end_date:
            print("❌ Both dates are required.")
            return

        query = {
            "range": {
                selected_field: {
                    "gte": start_date,
                    "lte": end_date
                }
            }
        }

        print(f"\n🔍 Prepared date range: {selected_field} from {start_date} to {end_date}")

        self.execute_or_show_query(query)

    def multi_field_search(self):
        """
        Search across multiple fields simultaneously.

        Example:
        - Search for "action" in genre AND "Christopher" in director
        - Or search same term across multiple fields
        """
        print("\n🔍 Multi-Field Search")
        print("-" * 30)
        print("1. Search SAME term across multiple fields")
        print("2. Search DIFFERENT terms in different fields")
        print("0. Back")

        choice = input("\n🎯 Choose option: ").strip()

        if choice == "1":
            self._same_term_multi_field()
        elif choice == "2":
            self._different_terms_multi_field()
        elif choice == "0":
            return
        else:
            print("❌ Invalid option.")

    def _same_term_multi_field(self):
        """Search same term across multiple selected fields."""
        fields, properties = self.get_fields_list()

        print("\n📋 Available Fields:\n")

        for i, field in enumerate(fields, start=1):
            field_type = properties[field].get('type', 'unknown')
            print(f"{i}. {field} ({field_type})")

        print("\n🔍 Select fields to search (comma-separated numbers)")
        print("   Example: 1,3,5")

        try:
            choices = input("\n🎯 Enter field numbers: ").strip()
            selected_indices = [int(x.strip()) - 1 for x in choices.split(',')]

            selected_fields = []
            for idx in selected_indices:
                if 0 <= idx < len(fields):
                    selected_fields.append(fields[idx])
                else:
                    print(f"❌ Invalid field number: {idx + 1}")
                    return

        except ValueError:
            print("❌ Please enter valid numbers.")
            return

        if not selected_fields:
            print("❌ No fields selected.")
            return

        print(f"\n✅ Selected fields: {', '.join(selected_fields)}")

        search_term = input(f"\n🔍 Enter search term: ")

        query = {
            "multi_match": {
                "query": search_term,
                "fields": selected_fields,
                "type": "best_fields"
            }
        }

        print(f"\n🔍 Prepared multi-field search for '{search_term}' across {len(selected_fields)} fields")

        self.execute_or_show_query(query)

    def _different_terms_multi_field(self):
        """Search different terms in different fields using bool query."""
        fields, properties = self.get_fields_list()

        print("\n📋 Available Fields:\n")

        for i, field in enumerate(fields, start=1):
            field_type = properties[field].get('type', 'unknown')
            print(f"{i}. {field} ({field_type})")

        must_conditions = []

        while True:
            print("\n" + "-" * 30)
            print(f"📋 Current conditions: {len(must_conditions)}")
            print("-" * 30)

            selected_field = self.select_field(fields, "Choose field (0 to finish): ")

            if selected_field is None:
                break

            value = input(f"🔍 Enter value for '{selected_field}': ")

            must_conditions.append({
                "match": {
                    selected_field: value
                }
            })

            print(f"✅ Added: {selected_field} = {value}")

            continue_adding = input("\n➕ Add another condition? (y/n): ").strip().lower()
            if continue_adding != 'y':
                break

        if not must_conditions:
            print("❌ No conditions specified.")
            return

        query = {
            "bool": {
                "must": must_conditions
            }
        }

        print(f"\n🔍 Prepared bool query with {len(must_conditions)} conditions")

        self.execute_or_show_query(query)

    def show_document_count(self):
        """
        Display total document count.
        """

        count = self.es.count(self.index_name)

        print(f"\n📊 Total Documents in '{self.index_name}': {count}")

    def show_sample_documents(self):
        """
        Show a few sample documents from the index.
        """
        try:
            sample_size = int(input("\n🎲 How many sample documents? (default=3): ").strip() or "3")
        except ValueError:
            print("❌ Invalid number, using default (3).")
            sample_size = 3

        query = {
            "match_all": {}
        }

        results = self.es.search(
            index_name=self.index_name,
            query=query
        )

        # Limit to requested sample size
        if results:
            results = results[:sample_size]
            print(f"\n🎲 Showing {len(results)} sample document(s):\n")
            self.print_results(results)
        else:
            print("\n📭 No documents found in index.")

    def manage_result_indexes(self):
        """
        Manage and delete result indexes created for Kibana.
        """
        print("\n" + "=" * 50)
        print("🗑️  MANAGE RESULT INDEXES")
        print("=" * 50)

        # فقط ایندکس‌هایی که _results_ توی اسمشون هست رو نشون بده
        all_indexes = self.es.get_indexes()

        result_indexes = [
            idx for idx in all_indexes
            if '_results_' in idx
        ]

        if not result_indexes:
            print("\n📭 No result indexes found!")
            return

        print("\n📋 Result Indexes (created for Kibana):\n")
        for i, idx in enumerate(result_indexes, start=1):
            # تعداد داکیومنت‌های هر ایندکس رو نشون بده
            try:
                count = self.es.count(idx)
                print(f"{i}. {idx} ({count} documents)")
            except:
                print(f"{i}. {idx}")

        print("\n" + "-" * 50)
        print("1. 🗑️  Delete specific index")
        print("2. 🗑️  Delete ALL result indexes")
        print("0. 🔙 Back")
        print("-" * 50)

        choice = input("\n🎯 Choose option: ").strip()

        if choice == "1":
            # پاک کردن یک ایندکس خاص
            try:
                idx_num = int(input(f"\n📝 Enter index number (1-{len(result_indexes)}): "))

                if 1 <= idx_num <= len(result_indexes):
                    index_to_delete = result_indexes[idx_num - 1]

                    confirm = input(f"\n⚠️  Delete '{index_to_delete}'? (y/n): ").strip().lower()

                    if confirm == 'y':
                        self.es.delete_index(index_to_delete)
                        print(f"✅ Deleted: {index_to_delete}")
                    else:
                        print("🔙 Cancelled.")
                else:
                    print("❌ Invalid index number!")

            except ValueError:
                print("❌ Please enter a valid number!")

        elif choice == "2":
            # پاک کردن همه ایندکس‌های نتایج
            print(f"\n⚠️  This will delete {len(result_indexes)} indexes!")
            confirm = input("🗑️  Type 'DELETE ALL' to confirm: ").strip()

            if confirm == "DELETE ALL":
                for idx in result_indexes:
                    try:
                        self.es.delete_index(idx)
                        print(f"✅ Deleted: {idx}")
                    except Exception as e:
                        print(f"❌ Failed to delete {idx}: {e}")
                print("\n✅ All result indexes deleted!")
            else:
                print("🔙 Cancelled. You must type 'DELETE ALL' exactly.")

        elif choice == "0":
            return

        else:
            print("❌ Invalid option!")
