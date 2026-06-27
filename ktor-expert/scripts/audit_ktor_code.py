#!/usr/bin/env python3
import argparse
import re
from pathlib import Path
from typing import List, Tuple

class KtorAuditor:
    def __init__(self, root_dir: str):
        self.root_path = Path(root_dir)
        self.violations: List[Tuple[Path, int, str, str]] = []

    def audit(self):
        if not self.root_path.exists():
            print(f"Error: Path {self.root_path} does not exist.")
            return

        for path in self.root_path.rglob("*.kt"):
            if "build/" in path.parts or ".gradle/" in path.parts:
                continue
            self._audit_file(path)

    def _audit_file(self, path: Path):
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            return  # skip unreadable files

        lines = content.splitlines()
        
        # Check for local HttpClient instantiation
        in_function = False
        client_in_func_regex = re.compile(r"\bval\s+\w+\s*=\s*HttpClient\b")
        func_start_regex = re.compile(r"\bfun\s+\w+")
        
        # Check for CIO client on mobile targets
        is_mobile_target = any(part in path.parts for part in ("androidMain", "iosMain", "commonMain"))
        cio_client_regex = re.compile(r"\bHttpClient\s*\(\s*CIO\s*\)")

        # Check for missing cancelCallOnClose in servers
        has_server_routing = "routing {" in content
        has_request_lifecycle = "HttpRequestLifecycle" in content or "cancelCallOnClose" in content

        # Check for refreshTokens missing markAsRefreshTokenRequest
        has_refresh_tokens = "refreshTokens {" in content
        has_mark_refresh = "markAsRefreshTokenRequest()" in content

        # Check for StatusPages (security exception mapping to avoid package leaks)
        has_status_pages = "StatusPages" in content

        for line_num, line in enumerate(lines, 1):
            # Check for local HttpClient instantiations
            if func_start_regex.search(line):
                in_function = True
            
            # Simple brace tracker to reset in_function (terse approximation)
            if in_function and line.strip() == "}":
                in_function = False

            if in_function and client_in_func_regex.search(line):
                # Ensure it's not a mock engine or test application client
                if "MockEngine" not in line and "createClient" not in line:
                    self.violations.append((
                        path, line_num, line.strip(),
                        "HttpClient created inside function. Potential leak. Reuse as application singleton."
                    ))

            # CIO client on mobile warning
            if is_mobile_target and cio_client_regex.search(line):
                self.violations.append((
                    path, line_num, line.strip(),
                    "CIO client engine used in mobile target. OkHttp/Darwin preferred for HTTP/2."
                ))

            # Missing markAsRefreshTokenRequest inside refreshTokens
            if has_refresh_tokens and "refreshTokens" in line and not has_mark_refresh:
                self.violations.append((
                    path, line_num, line.strip(),
                    "refreshTokens block exists but 'markAsRefreshTokenRequest()' was not found in file. Check for infinite loops."
                ))

        # File-level checks
        if has_server_routing:
            if not has_request_lifecycle:
                self.violations.append((
                    path, 1, "File contains routing block",
                    "Ktor server routing found but HttpRequestLifecycle with cancelCallOnClose = true is missing. Client disconnects will not cancel coroutines."
                ))
            if not has_status_pages:
                self.violations.append((
                    path, 1, "File contains routing block",
                    "Ktor server routing found but StatusPages plugin is missing. Security risk: raw exceptions may leak package structure."
                ))

    def report(self):
        if not self.violations:
            print("No Ktor anti-patterns detected.")
            return

        print(f"Found {len(self.violations)} potential Ktor issues:\n")
        current_file = None
        for path, line_num, code, msg in sorted(self.violations, key=lambda x: (x[0], x[1])):
            rel_path = path.relative_to(self.root_path) if self.root_path != path else path.name
            if rel_path != current_file:
                print(f"\n[{rel_path}]")
                current_file = rel_path
            print(f"  Line {line_num}: {code}")
            print(f"    -> {msg}")

def main():
    parser = argparse.ArgumentParser(description="Audit Kotlin files for Ktor best practices and footguns.")
    parser.add_argument("path", help="Directory or file path to scan")
    args = parser.parse_args()
    
    auditor = KtorAuditor(args.path)
    auditor.audit()
    auditor.report()

if __name__ == "__main__":
    main()
