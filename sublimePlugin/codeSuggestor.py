import sublime
import sublime_plugin
import os
import sys

# Add the plugin directory to Python path to import our modules
plugin_dir = os.path.dirname(os.path.abspath(__file__))
if plugin_dir not in sys.path:
    sys.path.append(plugin_dir)

# Import our modules
try:
    from code_explainer import CodeExplainer
    EXPLAINER = None  # Will be lazily initialized
except ImportError as e:
    print(f"CodeSuggester: Error importing modules: {e}")
    EXPLAINER = None


class ExplainCodeCommand(sublime_plugin.TextCommand):
    """Command to explain selected code or entire file"""
    
    def run(self, edit):
        # Get the code to explain
        code = self._get_code_to_explain()
        
        if not code:
            sublime.status_message("No code to explain")
            return
        
        # Show loading message
        sublime.status_message("Analyzing code...")
        
        # Run explanation in a separate thread to avoid blocking UI
        sublime.set_timeout_async(lambda: self._explain_code_async(code), 0)
    
    def _get_code_to_explain(self):
        """Get code from selection or entire file"""
        # Check if there's a selection
        selection = self.view.sel()
        if selection and len(selection) > 0:
            region = selection[0]
            if not region.empty():
                return self.view.substr(region)
        
        # No selection, use entire file
        return self.view.substr(sublime.Region(0, self.view.size()))
    
    def _explain_code_async(self, code):
        """Run explanation asynchronously"""
        global EXPLAINER
        
        try:
            # Lazily initialize explainer
            if EXPLAINER is None:
                EXPLAINER = CodeExplainer()
            
            # Generate explanation
            explanation = EXPLAINER.explain_code(code)
            
            # Show in new view
            sublime.set_timeout(lambda: self._show_explanation(explanation), 0)
            
        except Exception as e:
            error_msg = f"Error explaining code: {str(e)}"
            print(error_msg)
            sublime.set_timeout(lambda: sublime.error_message(error_msg), 0)
    
    def _show_explanation(self, explanation):
        """Display explanation in a new view"""
        # Create new view
        window = self.view.window()
        if not window:
            return
        
        explanation_view = window.new_file()
        explanation_view.set_name("Code Explanation")
        explanation_view.set_scratch(True)  # Don't prompt to save
        explanation_view.set_syntax_file("Packages/Text/Plain text.tmLanguage")
        
        # Insert explanation
        explanation_view.run_command('insert_explanation_text', {'text': explanation})
        
        # Set read-only
        explanation_view.set_read_only(True)
        
        sublime.status_message("Explanation generated!")
    
    def is_enabled(self):
        """Only enable for Python files"""
        return self.view.match_selector(0, "source.python")


class InsertExplanationTextCommand(sublime_plugin.TextCommand):
    """Helper command to insert text in explanation view"""
    
    def run(self, edit, text):
        self.view.insert(edit, 0, text)


class ExplainCodeOnSaveListener(sublime_plugin.EventListener):
    """Optional: Auto-explain on save"""
    
    def on_post_save_async(self, view):
        # Only for Python files
        if not view.match_selector(0, "source.python"):
            return
        
        # Check if auto-explain is enabled in settings
        settings = sublime.load_settings("CodeSuggester.sublime-settings")
        if not settings.get("auto_explain_on_save", False):
            return
        
        # Run explanation
        view.run_command('explain_code')


class CodeSuggesterQuickPanelCommand(sublime_plugin.WindowCommand):
    """Quick panel for various code analysis options"""
    
    def run(self):
        options = [
            "Explain Current File",
            "Explain Selection",
            "Show Function Database Info",
            "Rebuild Function Database"
        ]
        
        self.window.show_quick_panel(options, self._on_select)
    
    def _on_select(self, index):
        if index == -1:
            return
        
        if index == 0:
            # Explain current file
            view = self.window.active_view()
            if view:
                view.run_command('explain_code')
        
        elif index == 1:
            # Explain selection
            view = self.window.active_view()
            if view:
                view.run_command('explain_code')
        
        elif index == 2:
            # Show database info
            sublime.set_timeout_async(self._show_database_info, 0)
        
        elif index == 3:
            # Rebuild database
            sublime.set_timeout_async(self._rebuild_database, 0)
    
    def _show_database_info(self):
        """Show information about the function database"""
        try:
            from embedder import FunctionEmbedder
            
            embedder = FunctionEmbedder()
            database_path = os.path.join(plugin_dir, 'os_function_database.json')
            
            if embedder.load_database(database_path):
                info = f"Function Database Info:\n\n"
                info += f"Database Path: {database_path}\n"
                info += f"Total Functions: {len(embedder.function_database)}\n"
                info += f"Embedding Dimensions: {embedder.embeddings.shape[1]}\n"
                
                sublime.message_dialog(info)
            else:
                sublime.error_message("Database not found. Please rebuild.")
        
        except Exception as e:
            sublime.error_message(f"Error loading database info: {str(e)}")
    
    def _rebuild_database(self):
        """Rebuild the function database"""
        try:
            from embedder import build_os_library_database
            
            sublime.status_message("Building function database...")
            
            # Change to plugin directory
            original_dir = os.getcwd()
            os.chdir(plugin_dir)
            
            # Build database
            build_os_library_database()
            
            # Restore directory
            os.chdir(original_dir)
            
            sublime.message_dialog("Database rebuilt successfully!")
        
        except Exception as e:
            sublime.error_message(f"Error rebuilding database: {str(e)}")


class ShowFunctionInfoCommand(sublime_plugin.TextCommand):
    """Show information about function under cursor"""
    
    def run(self, edit):
        # Get word under cursor
        word_region = self.view.word(self.view.sel()[0])
        word = self.view.substr(word_region)
        
        # Run async
        sublime.set_timeout_async(lambda: self._show_info_async(word), 0)
    
    def _show_info_async(self, function_name):
        """Show function info asynchronously"""
        global EXPLAINER
        
        try:
            if EXPLAINER is None:
                EXPLAINER = CodeExplainer()
            
            # Search for function
            results = EXPLAINER.embedder.find_similar_functions(function_name, top_k=1)
            
            if results:
                func_info = results[0]['function']
                similarity = results[0]['similarity']
                
                info = f"Function: {func_info['name']}\n\n"
                info += f"Signature: {func_info['signature']}\n\n"
                info += f"Description:\n{func_info['description']}\n\n"
                info += f"Match Confidence: {similarity:.2%}"
                
                sublime.set_timeout(lambda: sublime.message_dialog(info), 0)
            else:
                sublime.set_timeout(
                    lambda: sublime.status_message(f"No info found for '{function_name}'"),
                    0
                )
        
        except Exception as e:
            error_msg = f"Error retrieving function info: {str(e)}"
            print(error_msg)
            sublime.set_timeout(lambda: sublime.error_message(error_msg), 0)
    
    def is_enabled(self):
        return self.view.match_selector(0, "source.python")


def plugin_loaded():
    """Called when plugin is loaded"""
    print("CodeSuggester plugin loaded!")
    
    # Check if database exists
    database_path = os.path.join(plugin_dir, 'os_function_database.json')
    if not os.path.exists(database_path):
        print("Warning: Function database not found")
        print(f"Expected location: {database_path}")
        print("Run 'CodeSuggester: Rebuild Database' to create it")


def plugin_unloaded():
    """Called when plugin is unloaded"""
    print("CodeSuggester plugin unloaded")