import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from .models import MCPServerConfig
from .connectors import WordPressConnector, VPSConnector, StdioMCPConnector

DATA_DIR = Path("data/mcp")
CONFIG_FILE = DATA_DIR / "servers.json"

DEFAULT_TEMPLATES = [
    {
        "name": "wordpress-production",
        "category": "wordpress",
        "description": "Publication d'articles, gestion des médias et du contenu WordPress via WP REST API",
        "transport": "builtin",
        "url": "https://votre-site-wordpress.com",
        "env": {
            "WP_USERNAME": "admin",
            "WP_APP_PASSWORD": "xxxx xxxx xxxx xxxx"
        }
    },
    {
        "name": "vps-production",
        "category": "vps",
        "description": "Exécution de commandes shell, inspection Docker et maintenance VPS via SSH",
        "transport": "builtin",
        "env": {
            "VPS_HOST": "192.168.1.100",
            "VPS_USER": "root",
            "VPS_PORT": "22",
            "VPS_KEY_PATH": "C:/Users/piopi/.ssh/id_rsa"
        }
    },
    {
        "name": "github",
        "category": "github",
        "description": "Interaction avec dépôts, issues, pull requests et commits GitHub",
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "env": {
            "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_xxxxxxxxxxxxxxxxxxxx"
        }
    }
]

class MCPManager:
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or CONFIG_FILE
        self._ensure_storage()

    def _ensure_storage(self):
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.config_path.exists():
            initial_servers = {
                "github": {
                    "name": "github",
                    "category": "github",
                    "description": "Serveur officiel GitHub MCP pour exploration et modifications de code",
                    "transport": "stdio",
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-github"],
                    "env": {},
                    "enabled": True,
                    "status": "connected",
                    "tools": [
                        {"name": "create_or_update_file", "description": "Créer ou mettre à jour un fichier dans un repo GitHub"},
                        {"name": "search_repositories", "description": "Rechercher des dépôts sur GitHub"},
                        {"name": "create_issue", "description": "Créer une issue sur un dépôt GitHub"}
                    ]
                },
                "wordpress": {
                    "name": "wordpress",
                    "category": "wordpress",
                    "description": "Connecteur WordPress pour vibecoding, rédaction et publication d'articles",
                    "transport": "builtin",
                    "url": "https://example.com",
                    "env": {
                        "WP_USERNAME": "admin",
                        "WP_APP_PASSWORD": "xxxx xxxx xxxx xxxx"
                    },
                    "enabled": False,
                    "status": "configured",
                    "tools": WordPressConnector.get_tools()
                },
                "vps-server": {
                    "name": "vps-server",
                    "category": "vps",
                    "description": "Connecteur VPS pour exécution distante, vibecoding et Docker",
                    "transport": "builtin",
                    "env": {
                        "VPS_HOST": "127.0.0.1",
                        "VPS_USER": "root",
                        "VPS_PORT": "22"
                    },
                    "enabled": False,
                    "status": "configured",
                    "tools": VPSConnector.get_tools()
                }
            }
            self._save_raw(initial_servers)

    def _load_raw(self) -> Dict[str, Dict[str, Any]]:
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_raw(self, data: Dict[str, Dict[str, Any]]):
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def list_servers(self) -> List[Dict[str, Any]]:
        raw = self._load_raw()
        return list(raw.values())

    def get_server(self, name: str) -> Optional[Dict[str, Any]]:
        raw = self._load_raw()
        return raw.get(name)

    def add_or_update_server(self, data: Dict[str, Any]) -> Dict[str, Any]:
        name = data.get("name", "").strip()
        if not name:
            raise ValueError("Le nom du serveur MCP est obligatoire.")
        
        raw = self._load_raw()
        existing = raw.get(name, {})
        
        # Merge fields
        updated = {
            "name": name,
            "category": data.get("category", existing.get("category", "custom")),
            "description": data.get("description", existing.get("description", "")),
            "transport": data.get("transport", existing.get("transport", "stdio")),
            "command": data.get("command", existing.get("command")),
            "args": data.get("args", existing.get("args", [])),
            "env": data.get("env", existing.get("env", {})),
            "url": data.get("url", existing.get("url")),
            "headers": data.get("headers", existing.get("headers", {})),
            "enabled": data.get("enabled", existing.get("enabled", True)),
            "status": existing.get("status", "configured"),
            "last_tested": existing.get("last_tested"),
            "last_error": existing.get("last_error"),
            "tools": existing.get("tools", [])
        }
        
        # Populate default tools if category is recognized and tools are empty
        if not updated["tools"]:
            if updated["category"] == "wordpress":
                updated["tools"] = WordPressConnector.get_tools()
            elif updated["category"] == "vps":
                updated["tools"] = VPSConnector.get_tools()

        raw[name] = updated
        self._save_raw(raw)
        return updated

    def delete_server(self, name: str) -> bool:
        raw = self._load_raw()
        if name in raw:
            del raw[name]
            self._save_raw(raw)
            return True
        return False

    def toggle_server(self, name: str, enabled: bool) -> Optional[Dict[str, Any]]:
        raw = self._load_raw()
        if name in raw:
            raw[name]["enabled"] = enabled
            self._save_raw(raw)
            return raw[name]
        return None

    def test_server(self, name: str) -> Dict[str, Any]:
        raw = self._load_raw()
        server = raw.get(name)
        if not server:
            return {"success": False, "message": f"Serveur '{name}' introuvable."}

        cat = server.get("category", "")
        transport = server.get("transport", "stdio")
        now_iso = datetime.now(timezone.utc).isoformat()

        # 1. WordPress Connector
        if cat == "wordpress":
            success, msg, tools = WordPressConnector.test_connection(
                url=server.get("url", ""),
                env=server.get("env", {})
            )
            server["status"] = "connected" if success else "error"
            server["last_tested"] = now_iso
            server["last_error"] = None if success else msg
            if tools: server["tools"] = tools
            self._save_raw(raw)
            return {"success": success, "status": "connected" if success else "error", "message": msg, "tools": tools}

        # 2. VPS Connector
        elif cat == "vps":
            success, msg, tools = VPSConnector.test_connection(
                env=server.get("env", {})
            )
            server["status"] = "connected" if success else "error"
            server["last_tested"] = now_iso
            server["last_error"] = None if success else msg
            if tools: server["tools"] = tools
            self._save_raw(raw)
            return {"success": success, "status": "connected" if success else "error", "message": msg, "tools": tools}

        # 3. Generic Stdio
        elif transport == "stdio":
            success, msg, tools = StdioMCPConnector.test_and_discover_tools(
                command=server.get("command", ""),
                args=server.get("args", []),
                env=server.get("env", {})
            )
            server["status"] = "connected" if success else "error"
            server["last_tested"] = now_iso
            server["last_error"] = None if success else msg
            if tools: server["tools"] = tools
            self._save_raw(raw)
            return {"success": success, "status": "connected" if success else "error", "message": msg, "tools": tools}

        # 4. HTTP / SSE
        else:
            server["status"] = "connected"
            server["last_tested"] = now_iso
            self._save_raw(raw)
            return {"success": True, "status": "connected", "message": "Serveur configuré.", "tools": server.get("tools", [])}

    def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        server = self.get_server(server_name)
        if not server:
            return {"error": f"Serveur MCP '{server_name}' introuvable."}
        if not server.get("enabled", True):
            return {"error": f"Le serveur MCP '{server_name}' est désactivé."}

        cat = server.get("category", "")
        if cat == "wordpress":
            return WordPressConnector.execute_tool(
                tool_name=tool_name,
                args=arguments,
                url=server.get("url", ""),
                env=server.get("env", {})
            )
        elif cat == "vps":
            return VPSConnector.execute_tool(
                tool_name=tool_name,
                args=arguments,
                env=server.get("env", {})
            )

        return {"error": f"L'exécution directe de l'outil '{tool_name}' sur ce transport n'est pas supportée nativement."}

    @staticmethod
    def get_templates() -> List[Dict[str, Any]]:
        return DEFAULT_TEMPLATES
