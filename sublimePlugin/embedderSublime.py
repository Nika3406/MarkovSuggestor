"""
Plugin-side embedder loader.

Provides:
- FunctionEmbedder class with load_database(path) and find_similar_functions(query, top_k=3)
- build_os_library_database() to (re)create os_function_database.json by searching for os_info.txt
"""

import os
import json
import math
import threading

try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
except Exception:
    # Defer imports; the plugin may not have these packages. Caller must handle errors.
    np = None
    SentenceTransformer = None

PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_NAME = 'os_function_database.json'

def _cosine_sim(a, b):
    # a,b are 1D numpy arrays
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)

class FunctionEmbedder:
    def __init__(self, model_name=None):
        self.database_path = None
        self.function_database = []
        self.embeddings = None
        self.model_name = model_name
        self.model = None

    def load_database(self, path=None):
        """Load database JSON and prepare embeddings as numpy array."""
        db_path = path or os.path.join(PLUGIN_DIR, DEFAULT_DB_NAME)
        self.database_path = db_path
        if not os.path.exists(db_path):
            return False

        with open(db_path, 'r', encoding='utf-8') as f:
            db = json.load(f)

        self.function_database = db.get('entries', [])
        self.model_name = db.get('meta', {}).get('model', self.model_name)

        # build embeddings array
        try:
            import numpy as np
            self.embeddings = np.array([entry['embedding'] for entry in self.function_database], dtype=float)
        except Exception:
            self.embeddings = None

        return True

    def ensure_model(self):
        if self.model is None:
            if SentenceTransformer is None:
                raise RuntimeError("sentence-transformers not available in plugin runtime")
            # prefer model specified in DB if present
            model_name = self.model_name or "all-MiniLM-L6-v2"
            self.model = SentenceTransformer(model_name)

    def find_similar_functions(self, query, top_k=3):
        """Return top_k matches for a query string.
        Each result is a dict: {'function': entry, 'similarity': score}
        """
        if not self.function_database or self.embeddings is None:
            raise RuntimeError("Database not loaded")

        self.ensure_model()

        # compute embedding
        query_emb = self.model.encode([query], convert_to_numpy=True)[0]

        # compute cosine similarity
        import numpy as np
        sims = []
        for idx, emb in enumerate(self.embeddings):
            sims.append((_cosine_sim(query_emb, emb), idx))
        sims.sort(reverse=True, key=lambda x: x[0])

        results = []
        for sim, idx in sims[:top_k]:
            results.append({'function': self.function_database[idx], 'similarity': sim})
        return results

def build_os_library_database(target_path=None, verbose=True):
    """
    Attempt to locate DataSetup/os_info.txt by searching parent folders and build database inside plugin dir.
    """
    # try a few likely locations
    search_paths = [
        os.path.join(PLUGIN_DIR, 'os_info.txt'),
        os.path.join(PLUGIN_DIR, '..', 'DataSetup', 'os_info.txt'),
        os.path.join(PLUGIN_DIR, '..', '..', 'DataSetup', 'os_info.txt'),
        os.path.join(os.getcwd(), 'DataSetup', 'os_info.txt'),
    ]
    found = None
    for p in search_paths:
        p = os.path.abspath(p)
        if os.path.exists(p):
            found = p
            break

    if not found:
        raise FileNotFoundError("Could not find os_info.txt. Searched: {}".format(search_paths))

    out = target_path or os.path.join(PLUGIN_DIR, DEFAULT_DB_NAME)

    # Try to reuse DataSetup/embedder.py if available (preferred)
    data_setup_embedder = None
    try:
        import importlib.util
        ds_path = os.path.abspath(os.path.join(PLUGIN_DIR, '..', 'DataSetup', 'embedder.py'))
        if os.path.exists(ds_path):
            spec = importlib.util.spec_from_file_location("data_embedder", ds_path)
            ds = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(ds)
            data_setup_embedder = ds
    except Exception:
        data_setup_embedder = None

    if data_setup_embedder:
        # call its build_database
        if verbose:
            print("Using DataSetup/embedder.py to build DB from", found)
        data_setup_embedder.build_database(found, out)
        return out

    # Fallback: do a minimal inlined build (requires sentence-transformers)
    if SentenceTransformer is None:
        raise RuntimeError("sentence-transformers is not installed. Install in the environment used by Sublime or build the DB offline using DataSetup/embedder.py")

    # Use DataSetup parsing logic inline (basic)
    with open(found, 'r', encoding='utf-8') as f:
        text = f.read()

    # naive split by "Function:" and "Class:"
    parts = re.split(r'(?:^|\n)(Function:|Class:)', text)
    # not perfect — recommend using DataSetup/embedder.py to build DB offline
    raise RuntimeError("Please build the database offline with DataSetup/embedder.py and put os_function_database.json inside the plugin folder.")
