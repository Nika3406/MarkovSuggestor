class FileManager:
    def __init__(self, file: str):
        self.file = file
    
    def get_imports(self):
        imports = []

        for line in self.file.splitlines():
            line_tokens = line.split(' ')
            if line_tokens[0] == "import":
                for token in line_tokens[1:]:
                    parsed_token = token.replace(',', '')
                    if len(parsed_token) != 0:
                        imports.append(parsed_token)

        return imports