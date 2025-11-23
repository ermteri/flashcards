# app.py – now with permanent storage across server restarts
from flask import Flask, render_template, jsonify, request
import json
import random
import os

app = Flask(__name__)

CARDS_FILE = 'cards.json'
FAILED_FILE = 'failed.json'      # ← NEW: persistent failed list
SESSION_SIZE = 50

def load_cards():
    with open(CARDS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

# NEW: load and save failed indices to disk
def load_failed_indices():
    if os.path.exists(FAILED_FILE):
        with open(FAILED_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return set(data.get('failed_indices', []))
    return set()

def save_failed_indices(indices):
    with open(FAILED_FILE, 'w', encoding='utf-8') as f:
        json.dump({'failed_indices': sorted(indices)}, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/failed', methods=['GET'])
def get_failed():
    return jsonify({'failed_indices': sorted(load_failed_indices())})

@app.route('/api/failed', methods=['POST'])
def save_failed():
    data = request.get_json()
    indices = set(data.get('failed_indices', []))
    save_failed_indices(indices)
    return jsonify({'status': 'saved', 'count': len(indices)})

@app.route('/api/cards', methods=['GET'])
def get_quiz_cards():
    all_cards = load_cards()
    if not all_cards:
        return jsonify([])

    failed_indices = load_failed_indices()

    failed_items = []
    for i in failed_indices:
        if i < len(all_cards):
            failed_items.append({"card": all_cards[i], "original_index": i})

    random.shuffle(failed_items)

    remaining = [
        {"card": card, "original_index": idx}
        for idx, card in enumerate(all_cards)
        if idx not in failed_indices
    ]
    random.shuffle(remaining)
    needed = SESSION_SIZE - len(failed_items)
    random_items = remaining[:max(0, needed)]

    deck = failed_items + random_items

    result = []
    for item in deck:
        c = item["card"]
        result.append({
            "index": item["original_index"],
            "front": c["front"],
            "back": c["back"],
            "pinyin": c.get("pinyin", "")   # ← DEN HÄR RADEN ÄR NYCKELN!
        })

    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
