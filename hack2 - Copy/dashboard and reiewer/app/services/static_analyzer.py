import ast
import re
from typing import List, Dict, Any


class StaticAnalyzer:
    """Static code analysis using AST and heuristics"""
    
    def analyze_python(self, code: str) -> List[Dict[str, Any]]:
        """Analyze Python code using AST"""
        issues = []
        
        try:
            tree = ast.parse(code)
            
            # Check for common issues
            for node in ast.walk(tree):
                # Detect bare except clauses
                if isinstance(node, ast.ExceptHandler):
                    if node.type is None:
                        issues.append({
                            "severity": "warning",
                            "category": "style",
                            "line_number": node.lineno,
                            "description": "Bare except clause catches all exceptions, including system exits",
                            "suggestion": "Specify the exception type or use 'except Exception:'",
                            "confidence": 0.9
                        })
                
                # Detect mutable default arguments
                if isinstance(node, ast.FunctionDef):
                    for default in node.args.defaults:
                        if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                            issues.append({
                                "severity": "warning",
                                "category": "bug",
                                "line_number": node.lineno,
                                "description": "Mutable default argument can lead to unexpected behavior",
                                "suggestion": "Use None as default and initialize inside the function",
                                "confidence": 0.95
                            })
                
                # Detect unused variables (simple heuristic)
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id.startswith('_') and not target.id.startswith('__'):
                            # This is a convention for unused variables
                            pass
        
        except SyntaxError as e:
            issues.append({
                "severity": "critical",
                "category": "bug",
                "line_number": e.lineno if hasattr(e, 'lineno') else None,
                "description": f"Syntax error: {str(e)}",
                "suggestion": "Fix the syntax error",
                "confidence": 1.0
            })
        
        return issues
    
    def analyze_javascript(self, code: str) -> List[Dict[str, Any]]:
        """Analyze JavaScript/TypeScript code using heuristics"""
        issues = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Detect == instead of ===
            if '==' in line and '===' not in line and '!=' in line and '!==' not in line:
                if not line.strip().startswith('//'):
                    issues.append({
                        "severity": "suggestion",
                        "category": "style",
                        "line_number": i,
                        "description": "Use === or !== for strict equality comparison",
                        "suggestion": "Replace == with === and != with !==",
                        "confidence": 0.8
                    })
            
            # Detect var usage
            if re.search(r'\bvar\b', line):
                if not line.strip().startswith('//'):
                    issues.append({
                        "severity": "suggestion",
                        "category": "style",
                        "line_number": i,
                        "description": "Use 'let' or 'const' instead of 'var'",
                        "suggestion": "Replace 'var' with 'let' or 'const'",
                        "confidence": 0.85
                    })
            
            # Detect console.log (potential debugging code)
            if 'console.log' in line:
                if not line.strip().startswith('//'):
                    issues.append({
                        "severity": "info",
                        "category": "style",
                        "line_number": i,
                        "description": "console.log statement found - may be debugging code",
                        "suggestion": "Remove or replace with proper logging",
                        "confidence": 0.7
                    })
        
        return issues
    
    def analyze_java(self, code: str) -> List[Dict[str, Any]]:
        """Analyze Java code using heuristics"""
        issues = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Detect System.out.println (debugging code)
            if 'System.out.println' in line:
                if not line.strip().startswith('//'):
                    issues.append({
                        "severity": "info",
                        "category": "style",
                        "line_number": i,
                        "description": "System.out.println found - use proper logging framework",
                        "suggestion": "Use a logging framework like SLF4J or Log4j",
                        "confidence": 0.8
                    })
            
            # Detect empty catch blocks
            if line.strip() == 'catch' or 'catch (' in line:
                # Simple heuristic - would need proper parsing for accuracy
                issues.append({
                    "severity": "warning",
                    "category": "bug",
                    "line_number": i,
                    "description": "Ensure catch block is not empty and handles exceptions properly",
                    "suggestion": "Add proper exception handling or logging",
                    "confidence": 0.6
                })
        
        return issues
    
    def analyze(self, code: str, language: str) -> List[Dict[str, Any]]:
        """Analyze code based on language"""
        language = language.lower()
        
        if language in ['python', 'py']:
            return self.analyze_python(code)
        elif language in ['javascript', 'js', 'typescript', 'ts', 'jsx', 'tsx']:
            return self.analyze_javascript(code)
        elif language == 'java':
            return self.analyze_java(code)
        else:
            return []


def get_static_analyzer() -> StaticAnalyzer:
    """Get static analyzer instance"""
    return StaticAnalyzer()
