# cleanup_results.py
from .elasticsearch_client import ElasticsearchClient


def cleanup_all_results():
    es = ElasticsearchClient()

    all_indexes = es.get_indexes()

    result_indexes = [idx for idx in all_indexes if '_results_' in idx]

    if not result_indexes:
        print("📭 No result indexes found!")
        return

    print(f"📋 Found {len(result_indexes)} result indexes:")
    for idx in result_indexes:
        count = es.count(idx)
        print(f"  - {idx} ({count} docs)")

    confirm = input("\n🗑️  Delete all? (y/n): ").strip().lower()

    if confirm == 'y':
        for idx in result_indexes:
            es.delete_index(idx)
            print(f"✅ Deleted: {idx}")
        print("\n✅ All cleaned up!")
    else:
        print("🔙 Cancelled.")


if __name__ == "__main__":
    cleanup_all_results()