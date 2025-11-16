from sentence_transformers import SentenceTransformer
import numpy as np
import json
import os

class FunctionEmbedder:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        """
        Initialize the embedder with a sentence transformer model
        
        Args:
            model_name: Name of the sentence-transformers model
                       'all-MiniLM-L6-v2' is fast and accurate (384 dim)
        """
        print(f"Loading sentence transformer model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.function_database = []
        self.embeddings = None
    
    def build_function_database(self, library_info_file):
        """
        Build function database from library info file (e.g., os_info.txt)
        
        Args:
            library_info_file: Path to the library info text file
        
        Returns:
            Number of functions indexed
        """
        print(f"Building function database from {library_info_file}")
        
        functions = self._parse_library_info(library_info_file)
        
        # Create embeddings for each function
        texts_to_embed = []
        for func in functions:
            # Combine name and description for rich semantic representation
            text = f"{func['name']}: {func['description']}"
            texts_to_embed.append(text)
            self.function_database.append(func)
        
        # Generate embeddings in batch (faster)
        print(f"Generating embeddings for {len(texts_to_embed)} functions...")
        self.embeddings = self.model.encode(texts_to_embed, show_progress_bar=True)
        
        print(f"✓ Database built with {len(self.function_database)} functions")
        return len(self.function_database)
    
    def _parse_library_info(self, filepath):
        """Parse the library info text file"""
        functions = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by function sections
        sections = content.split('Function: ')
        
        for section in sections[1:]:  # Skip header
            lines = section.split('\n')
            if len(lines) < 3:
                continue
            
            # Extract function name
            name = lines[0].strip()
            
            # Extract signature
            signature = ''
            description = ''
            
            for i, line in enumerate(lines):
                if line.startswith('Signature:'):
                    signature = line.replace('Signature:', '').strip()
                elif line.startswith('Description:'):
                    # Get all description lines
                    desc_lines = []
                    for j in range(i+1, len(lines)):
                        if lines[j].strip() and not lines[j].startswith('Function:'):
                            desc_lines.append(lines[j].strip())
                        else:
                            break
                    description = ' '.join(desc_lines)
                    break
            
            if name and description:
                functions.append({
                    'name': name,
                    'signature': signature,
                    'description': description[:500]  # Limit length
                })
        
        return functions
    
    def save_database(self, output_path='function_database.json'):
        """Save the function database and embeddings"""
        data = {
            'functions': self.function_database,
            'embeddings': self.embeddings.tolist() if self.embeddings is not None else []
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"✓ Database saved to {output_path}")
    
    def load_database(self, database_path='function_database.json'):
        """Load pre-built function database"""
        if not os.path.exists(database_path):
            print(f"Warning: Database file {database_path} not found")
            return False
        
        with open(database_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.function_database = data['functions']
        self.embeddings = np.array(data['embeddings'])
        
        print(f"✓ Loaded database with {len(self.function_database)} functions")
        return True
    
    def find_similar_functions(self, query, top_k=3):
        """
        Find similar functions based on semantic similarity
        
        Args:
            query: Query string (e.g., "list files in directory")
            top_k: Number of top matches to return
        
        Returns:
            List of matched functions with similarity scores
        """
        if self.embeddings is None or len(self.function_database) == 0:
            print("Warning: Database not loaded")
            return []
        
        # Encode query
        query_embedding = self.model.encode([query])[0]
        
        # Calculate cosine similarity
        similarities = self._cosine_similarity(query_embedding, self.embeddings)
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        # Build results
        results = []
        for idx in top_indices:
            results.append({
                'function': self.function_database[idx],
                'similarity': float(similarities[idx]),
                'rank': len(results) + 1
            })
        
        return results
    
    def match_function_call(self, function_call_info):
        """
        Match a function call from code to library functions
        
        Args:
            function_call_info: Dict with function call details
                               {'full_name': 'os.listdir', 'args': ['.']}
        
        Returns:
            Best matching function info
        """
        func_name = function_call_info.get('full_name', '')
        args = function_call_info.get('args', [])
        
        # Create query from function name and arguments
        query = func_name.replace('.', ' ').replace('_', ' ')
        if args:
            query += ' ' + ' '.join(str(arg) for arg in args)
        
        # Find matches
        matches = self.find_similar_functions(query, top_k=1)
        
        if matches:
            return matches[0]
        else:
            return None
    
    def _cosine_similarity(self, vec1, vec2_matrix):
        """Calculate cosine similarity between vector and matrix of vectors"""
        # Normalize
        vec1_norm = vec1 / np.linalg.norm(vec1)
        vec2_norms = vec2_matrix / np.linalg.norm(vec2_matrix, axis=1, keepdims=True)
        
        # Dot product
        similarities = np.dot(vec2_norms, vec1_norm)
        
        return similarities
    
    def embed_code_tokens(self, tokens):
        """
        Create embeddings for code tokens
        
        Args:
            tokens: List of code tokens
        
        Returns:
            Numpy array of embeddings
        """
        if not tokens:
            return np.array([])
        
        # Create meaningful text from tokens
        token_texts = [token.replace('_', ' ').replace('.', ' ') for token in tokens]
        
        # Generate embeddings
        embeddings = self.model.encode(token_texts)
        
        return embeddings


def build_os_library_database():
    """Helper function to build the os library database"""
    embedder = FunctionEmbedder()
    
    # Build from os_info.txt
    library_file = 'DataSetup/os_info.txt'
    if os.path.exists(library_file):
        embedder.build_function_database(library_file)
        embedder.save_database('os_function_database.json')
        print("\n✓ OS library database created successfully!")
    else:
        print(f"Error: {library_file} not found")
        print("Please ensure os_info.txt is in the current directory")


if __name__ == "__main__":
    # Build the database when run directly
    build_os_library_database()