import json
import os
import subprocess
import base64
import urllib.request
import urllib.error
from typing import Dict, Any, List, Tuple
from datetime import datetime, timezone

class WordPressConnector:
    """Native WordPress REST API bridge exposing standard MCP tools."""
    
    @staticmethod
    def _get_auth_header(env: Dict[str, str]) -> str:
        user = env.get("WP_USERNAME") or env.get("USERNAME") or ""
        app_pass = env.get("WP_APP_PASSWORD") or env.get("APP_PASSWORD") or env.get("PASSWORD") or ""
        token = f"{user}:{app_pass}".encode("utf-8")
        return f"Basic {base64.b64encode(token).decode('ascii')}"

    @staticmethod
    def _clean_url(url: str) -> str:
        url = url.strip()
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        return url.rstrip("/")

    @classmethod
    def test_connection(cls, url: str, env: Dict[str, str]) -> Tuple[bool, str, List[Dict[str, Any]]]:
        clean_url = cls._clean_url(url or env.get("WP_SITE_URL", ""))
        if not clean_url:
            return False, "URL WordPress manquante.", []
        
        target = f"{clean_url}/wp-json/wp/v2/users/me"
        req = urllib.request.Request(target)
        auth = cls._get_auth_header(env)
        req.add_header("Authorization", auth)
        req.add_header("User-Agent", "AgyStudio-MCP/2.6")

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                user_name = data.get("name", "Connecté")
                tools = cls.get_tools()
                return True, f"Connexion réussie à WordPress ({clean_url}) en tant que '{user_name}'.", tools
        except urllib.error.HTTPError as e:
            if e.code == 401 or e.code == 403:
                return False, f"Échec d'authentification ({e.code}) : Identifiants ou mot de passe d'application invalides.", []
            return False, f"Erreur HTTP WordPress {e.code} : {e.reason}", []
        except Exception as e:
            return False, f"Impossible de joindre le site WordPress : {e}", []

    @classmethod
    def get_tools(cls) -> List[Dict[str, Any]]:
        return [
            {
                "name": "wp_get_site_info",
                "description": "Obtenir les informations du site WordPress et de l'utilisateur actif.",
                "inputSchema": {"type": "object", "properties": {}}
            },
            {
                "name": "wp_list_posts",
                "description": "Lister les derniers articles (statut: publish, draft, pending).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "enum": ["publish", "draft", "any"], "default": "any"},
                        "per_page": {"type": "integer", "default": 10}
                    }
                }
            },
            {
                "name": "wp_create_post",
                "description": "Créer ou publier un article sur WordPress.",
                "inputSchema": {
                    "type": "object",
                    "required": ["title", "content"],
                    "properties": {
                        "title": {"type": "string", "description": "Titre de l'article"},
                        "content": {"type": "string", "description": "Contenu HTML ou texte"},
                        "status": {"type": "string", "enum": ["publish", "draft", "pending"], "default": "draft"}
                    }
                }
            },
            {
                "name": "wp_update_post",
                "description": "Mettre à jour un article existant par son ID.",
                "inputSchema": {
                    "type": "object",
                    "required": ["post_id"],
                    "properties": {
                        "post_id": {"type": "integer", "description": "ID de l'article"},
                        "title": {"type": "string"},
                        "content": {"type": "string"},
                        "status": {"type": "string", "enum": ["publish", "draft"]}
                    }
                }
            }
        ]

    @classmethod
    def execute_tool(cls, tool_name: str, args: Dict[str, Any], url: str, env: Dict[str, str]) -> Dict[str, Any]:
        clean_url = cls._clean_url(url or env.get("WP_SITE_URL", ""))
        auth = cls._get_auth_header(env)

        if tool_name == "wp_get_site_info":
            target = f"{clean_url}/wp-json/wp/v2/users/me"
            req = urllib.request.Request(target)
            req.add_header("Authorization", auth)
            with urllib.request.urlopen(req, timeout=12) as r:
                return json.loads(r.read().decode("utf-8"))

        elif tool_name == "wp_list_posts":
            status = args.get("status", "any")
            per_page = args.get("per_page", 10)
            target = f"{clean_url}/wp-json/wp/v2/posts?status={status}&per_page={per_page}"
            req = urllib.request.Request(target)
            req.add_header("Authorization", auth)
            with urllib.request.urlopen(req, timeout=12) as r:
                posts = json.loads(r.read().decode("utf-8"))
                return {
                    "count": len(posts),
                    "posts": [{"id": p.get("id"), "title": p.get("title", {}).get("rendered"), "status": p.get("status"), "link": p.get("link")} for p in posts]
                }

        elif tool_name == "wp_create_post":
            target = f"{clean_url}/wp-json/wp/v2/posts"
            payload = json.dumps({
                "title": args.get("title", ""),
                "content": args.get("content", ""),
                "status": args.get("status", "draft")
            }).encode("utf-8")
            req = urllib.request.Request(target, data=payload, headers={
                "Authorization": auth,
                "Content-Type": "application/json"
            })
            with urllib.request.urlopen(req, timeout=15) as r:
                res = json.loads(r.read().decode("utf-8"))
                return {
                    "success": True,
                    "id": res.get("id"),
                    "title": res.get("title", {}).get("rendered"),
                    "status": res.get("status"),
                    "url": res.get("link")
                }

        elif tool_name == "wp_update_post":
            post_id = args.get("post_id")
            target = f"{clean_url}/wp-json/wp/v2/posts/{post_id}"
            body_dict = {}
            if "title" in args: body_dict["title"] = args["title"]
            if "content" in args: body_dict["content"] = args["content"]
            if "status" in args: body_dict["status"] = args["status"]
            
            payload = json.dumps(body_dict).encode("utf-8")
            req = urllib.request.Request(target, data=payload, headers={
                "Authorization": auth,
                "Content-Type": "application/json"
            })
            with urllib.request.urlopen(req, timeout=15) as r:
                res = json.loads(r.read().decode("utf-8"))
                return {"success": True, "id": res.get("id"), "status": res.get("status"), "url": res.get("link")}

        return {"error": f"Outil '{tool_name}' non reconnu"}


class VPSConnector:
    """Native VPS/SSH bridge exposing standard MCP remote execution tools."""

    @classmethod
    def _build_ssh_cmd(cls, env: Dict[str, str], remote_cmd: str) -> List[str]:
        host = env.get("VPS_HOST") or env.get("HOST") or "localhost"
        user = env.get("VPS_USER") or env.get("USER") or "root"
        port = env.get("VPS_PORT") or env.get("PORT") or "22"
        key_path = env.get("VPS_KEY_PATH") or env.get("KEY_PATH") or ""

        cmd = ["ssh", "-p", str(port), "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=8"]
        if key_path and os.path.exists(key_path):
            cmd.extend(["-i", key_path])
        cmd.append(f"{user}@{host}")
        cmd.append(remote_cmd)
        return cmd

    @classmethod
    def test_connection(cls, env: Dict[str, str]) -> Tuple[bool, str, List[Dict[str, Any]]]:
        host = env.get("VPS_HOST") or env.get("HOST") or ""
        if not host:
            return False, "Hôte VPS (VPS_HOST) manquant.", []
        
        user = env.get("VPS_USER") or env.get("USER") or "root"
        test_cmd = cls._build_ssh_cmd(env, "echo 'AGY_VPS_READY'")
        try:
            res = subprocess.run(test_cmd, capture_output=True, text=True, timeout=10, encoding="utf-8")
            if "AGY_VPS_READY" in res.stdout:
                return True, f"Connexion SSH réussie à {user}@{host}.", cls.get_tools()
            else:
                err_msg = res.stderr.strip() or res.stdout.strip() or "Code de retour non nul"
                return False, f"Échec de connexion SSH : {err_msg}", []
        except subprocess.TimeoutExpired:
            return False, f"Délai d'attente dépassé (10s) pour joindre {host}.", []
        except Exception as e:
            return False, f"Erreur d'exécution SSH : {e}", []

    @classmethod
    def get_tools(cls) -> List[Dict[str, Any]]:
        return [
            {
                "name": "vps_run_command",
                "description": "Exécuter une commande shell/bash directement sur le serveur VPS distant.",
                "inputSchema": {
                    "type": "object",
                    "required": ["command"],
                    "properties": {
                        "command": {"type": "string", "description": "Commande bash à exécuter"}
                    }
                }
            },
            {
                "name": "vps_check_system",
                "description": "Vérifier l'état système du VPS (RAM, Disque, CPU, Uptime).",
                "inputSchema": {"type": "object", "properties": {}}
            },
            {
                "name": "vps_read_file",
                "description": "Lire le contenu d'un fichier sur le VPS distant.",
                "inputSchema": {
                    "type": "object",
                    "required": ["path"],
                    "properties": {
                        "path": {"type": "string", "description": "Chemin absolu du fichier"}
                    }
                }
            },
            {
                "name": "vps_check_docker",
                "description": "Lister les conteneurs Docker en cours d'exécution sur le VPS.",
                "inputSchema": {"type": "object", "properties": {}}
            }
        ]

    @classmethod
    def execute_tool(cls, tool_name: str, args: Dict[str, Any], env: Dict[str, str]) -> Dict[str, Any]:
        if tool_name == "vps_run_command":
            cmd_str = args.get("command", "")
            ssh_cmd = cls._build_ssh_cmd(env, cmd_str)
            res = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=30, encoding="utf-8")
            return {
                "stdout": res.stdout,
                "stderr": res.stderr,
                "exit_code": res.returncode
            }

        elif tool_name == "vps_check_system":
            sys_cmd = "uptime; echo '--- DISK ---'; df -h /; echo '--- MEMORY ---'; free -h"
            ssh_cmd = cls._build_ssh_cmd(env, sys_cmd)
            res = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=15, encoding="utf-8")
            return {"system_status": res.stdout}

        elif tool_name == "vps_read_file":
            p = args.get("path", "")
            ssh_cmd = cls._build_ssh_cmd(env, f"cat {p}")
            res = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=15, encoding="utf-8")
            return {"content": res.stdout, "error": res.stderr if res.returncode != 0 else None}

        elif tool_name == "vps_check_docker":
            ssh_cmd = cls._build_ssh_cmd(env, "docker ps --format 'table {{.ID}}\t{{.Image}}\t{{.Status}}\t{{.Names}}'")
            res = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=15, encoding="utf-8")
            return {"docker_containers": res.stdout}

        return {"error": f"Outil '{tool_name}' non reconnu"}


class StdioMCPConnector:
    """Generic JSON-RPC 2.0 stdio MCP client connector."""

    @classmethod
    def test_and_discover_tools(cls, command: str, args: List[str], env: Dict[str, str]) -> Tuple[bool, str, List[Dict[str, Any]]]:
        if not command:
            return False, "Commande non spécifiée pour le serveur stdio.", []

        full_cmd = [command] + (args or [])
        merged_env = os.environ.copy()
        merged_env.update(env or {})

        try:
            # Launch process with pipes
            proc = subprocess.Popen(
                full_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=merged_env,
                shell=False
            )

            # 1. Send initialize
            init_req = json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "AgyStudio", "version": "2.6"}
                }
            }) + "\n"
            proc.stdin.write(init_req)
            proc.stdin.flush()

            init_resp_line = proc.stdout.readline()
            if not init_resp_line:
                proc.kill()
                return False, "Le serveur MCP n'a pas répondu au handshake initialize.", []

            # 2. Send initialized notification
            notif = json.dumps({
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }) + "\n"
            proc.stdin.write(notif)
            proc.stdin.flush()

            # 3. Request tools/list
            tools_req = json.dumps({
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }) + "\n"
            proc.stdin.write(tools_req)
            proc.stdin.flush()

            tools_resp_line = proc.stdout.readline()
            proc.kill()

            if tools_resp_line:
                data = json.loads(tools_resp_line)
                tools = data.get("result", {}).get("tools", [])
                return True, f"Connecté avec succès. {len(tools)} outil(s) découvert(s).", tools
            return True, "Connecté avec succès (aucun outil retourné).", []

        except Exception as e:
            return False, f"Erreur lors du démarrage du serveur MCP : {e}", []
