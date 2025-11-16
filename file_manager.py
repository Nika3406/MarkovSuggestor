class FileManager:
    def __init__(self, file_path: str):
        with open(file_path, 'r') as file_data:
            self.file = file_data.read()
    
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
    
    def get_line(self, line_number):
        return self.file.split('\n')[line_number]
    
    def get_lines(self):
        lines = []
        for line_number in range(self.num_of_lines()):
            lines.append(self.get_line(line_number))

        return lines
    
    def functions_used(self, line_number):
        cache = ''
        functions = []
        in_string = False

        for let in self.get_line(line_number):
            if let == '\'' or let == '\"':
                in_string = not in_string
            if let == ' ' and not in_string:
                cache = ''
                continue
            if let == '(' and not in_string:
                functions += cache
                cache == ''
                continue
            if let == ')' and not in_string:
                continue
            if not in_string:
                cache += let

        return functions

    def num_of_lines(self):
        return len(self.file.split('\n'))