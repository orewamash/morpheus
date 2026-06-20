"""
examples/will_crash.py — A python script that intentionally crashes.
Used to test Morpheus exception capturing and logging.
"""


def process_item(item_list: list[int], index: int) -> int:
    # Will crash when index >= len(item_list)
    return item_list[index]


def run_loop():
    items = list(range(50))
    # Loop goes up to 60, provoking an IndexError at index 50
    for i in range(60):
        process_item(items, i)
        if i % 10 == 0:
            print(f"Processed up to {i}...")


if __name__ == "__main__":
    run_loop()
