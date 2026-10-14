import os
import json
import time
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any

from .base import (
    BaseAgentAdapter, AgentModel, AgentStatus, CapabilityStatus,
    ProviderDiagnostic, safe_run_process
)
from .hermes import HermesAdapter
from .antigravity import AntigravityAdapter
from .claude import ClaudeAdapter
from .codex import CodexAdapter
from .opencode import OpenCodeAdapter
from .qwen import QwenAdapter
from .cline import ClineAdapter
from .gemini import GeminiAdapter
from .custom import CustomAdapter

VALID_ROLES = [
    "ORCHESTRATOR", "PLANNER", "CODER", "RESEARCHER", "BROWSER",
    "TESTER", "REVIEWER", "SECURITY", "DOCUMENTATION", "PROJECT_MANAGER"
]

class AgentRegistry:
    def __init__(self, data_dir: Path, probe_ttl_seconds: int = 86400):
        self.data_dir = data_dir
        self.agents_file = data_dir / "agents.json"
        self.probe_ttl_seconds = probe_ttl_seconds
        self._builtin_adapters: Dict[str, BaseAgentAdapter] = {
            "hermes": HermesAdapter(),
            "agy": AntigravityAdapter(),
            "claude": ClaudeAdapter(),
            "codex": CodexAdapter(),
            "opencode": OpenCodeAdapter(),
            "qwen": QwenAdapter(),
            "cline": ClineAdapter(),
            "gemini": GeminiAdapter()
        }
        self._custom_adapters: Dict[str, CustomAdapter] = {}
        self._load_custom_adapters()

    def _load_data(self) -> Dict[str, Any]:
        if self.agents_file.exists():
            try:
                with open(self.agents_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"version": "2.0.0", "agents": {}}

    def _save_data(self, data: Dict[str, Any]):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with open(self.agents_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load_custom_adapters(self):
        data = self._load_data()
        for aid, adef in data.get("agents", {}).items():
            if adef.get("is_custom"):
                self._custom_adapters[aid] = CustomAdapter(
                    agent_id=aid,
                    name=adef.get("name", aid),
                    command=adef.get("command", aid),
                    custom_path=adef.get("path"),
                    version_args=adef.get("version_args", ["--version"]),
                    test_args=adef.get("test_args", ["-p", "{prompt}"]),
                    prompt_mode=adef.get("prompt_mode", "argument"),
                    timeout=adef.get("timeout", 120),
                    roles=adef.get("roles", ["CODER"]),
                    declared_capabilities=adef.get("declared_capabilities", {})
                )

    def get_adapter(self, agent_id: str) -> Optional[BaseAgentAdapter]:
        return self._builtin_adapters.get(agent_id) or self._custom_adapters.get(agent_id)

    def discover_all(self) -> List[Dict[str, Any]]:
        """
        Discovers all local agent CLIs, probes version and availability,
        preserves verified operational status and roles.
        """
        data = self._load_data()
        stored_agents = data.get("agents", {})
        results: Dict[str, Any] = {}

        all_adapters = list(self._builtin_adapters.values()) + list(self._custom_adapters.values())

        for adapter in all_adapters:
            existing = stored_agents.get(adapter.id)
            model = adapter.to_model(existing=existing, probe_ttl_seconds=self.probe_ttl_seconds)
            results[adapter.id] = model.model_dump()

        # Dynamic scan of PATH for popular external CLI tools if present
        extra_clis = ["ollama", "vllm", "aider", "sgpt"]
        for cli in extra_clis:
            if cli not in results and shutil.which(cli):
                cand_id = f"discovered_{cli}"
                if cand_id not in self._custom_adapters:
                    cad = CustomAdapter(
                        agent_id=cand_id,
                        name=f"{cli.upper()} CLI",
                        command=cli,
                        roles=["CODER", "RESEARCHER"]
                    )
                    self._custom_adapters[cand_id] = cad
                    m = cad.to_model(probe_ttl_seconds=self.probe_ttl_seconds)
                    m.is_custom = True
                    results[cand_id] = m.model_dump()

        data["agents"] = results
        data["last_discovery"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self._save_data(data)
        return list(results.values())

    def list_agents(self) -> List[Dict[str, Any]]:
        data = self._load_data()
        agents = data.get("agents", {})
        if not agents:
            return self.discover_all()
        return list(agents.values())

    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        data = self._load_data()
        agents = data.get("agents", {})
        if agent_id in agents:
            return agents[agent_id]
        adapter = self.get_adapter(agent_id)
        if adapter:
            model = adapter.to_model(probe_ttl_seconds=self.probe_ttl_seconds)
            agents[agent_id] = model.model_dump()
            data["agents"] = agents
            self._save_data(data)
            return model.model_dump()
        return None

    def agents_with_verified_capability(self, capability_name: str) -> List[Dict[str, Any]]:
        """
        Returns all OPERATIONAL agents that have verified status for the specified capability.
        Strictly checks verified operational health and capability status.
        Never infers unverified capabilities.
        """
        cap_clean = capability_name.strip().upper()
        matching = []
        for ag in self.list_agents():
            if ag.get("status") != AgentStatus.OPERATIONAL.value:
                continue
            caps = ag.get("capabilities", {})
            val = str(caps.get(cap_clean) or caps.get(cap_clean.lower()) or "").upper()
            if val == CapabilityStatus.VERIFIED.value:
                matching.append(ag)
        return matching

    def verify_agent(self, agent_id: str, provider_id: Optional[str] = None, timeout: int = 30) -> Dict[str, Any]:
        """
        Performs a REAL operational capability test for the specified agent CLI
        in an isolated temporary workspace (%TEMP%/AgyStudio/agent-probes/<id>).
        Supports specific provider targeting for multi-provider CLIs (e.g. Hermes + gemini).
        """
        adapter = self.get_adapter(agent_id)
        if not adapter:
            raise ValueError(f"Agent '{agent_id}' not found in registry")

        data = self._load_data()
        stored = data.get("agents", {}).get(agent_id, {})
        exe_path = adapter.discover()
        if not exe_path:
            raise FileNotFoundError(f"Executable for agent '{agent_id}' not found on machine")

        success, op_ev = adapter.probe(exe_path, timeout=timeout, provider_id=provider_id)
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # Update stored model
        agent_dict = self.get_agent(agent_id)
        if not agent_dict:
            agent_dict = adapter.to_model(existing=stored, probe_ttl_seconds=self.probe_ttl_seconds).model_dump()

        agent_dict["status"] = AgentStatus.OPERATIONAL.value if success else AgentStatus.FAILED.value
        agent_dict["last_checked"] = now
        agent_dict["last_verified"] = now if success else agent_dict.get("last_verified")
        agent_dict["operational_evidence"] = op_ev.model_dump()
        agent_dict["error"] = None if success else (op_ev.error or "Operational test failed")
        
        if op_ev.executable_identity and op_ev.executable_identity.version:
            agent_dict["version"] = op_ev.executable_identity.version
        if exe_path:
            agent_dict["path"] = str(exe_path)

        if op_ev.provider_id:
            agent_dict["active_provider"] = op_ev.provider_id

        if op_ev.executable_identity:
            agent_dict["executable_identity"] = op_ev.executable_identity.model_dump()
        if op_ev.configuration_fingerprint:
            agent_dict["configuration_fingerprint"] = op_ev.configuration_fingerprint
        if op_ev.capability_evidences:
            agent_dict["capability_evidences"] = {k: v.model_dump() for k, v in op_ev.capability_evidences.items()}

        # Update capabilities status to VERIFIED on success, or revert to non-operational on failure
        if success:
            for cap, status in adapter.get_capabilities(exe_path, operational=True).items():
                agent_dict.setdefault("capabilities", {})[cap] = status
        else:
            for cap, status in adapter.get_capabilities(exe_path, operational=False).items():
                agent_dict.setdefault("capabilities", {})[cap] = status

        data.setdefault("agents", {})[agent_id] = agent_dict
        self._save_data(data)
        return agent_dict

    def bind_role(self, agent_id: str, role: str, enabled: bool) -> Dict[str, Any]:
        if role not in VALID_ROLES:
            raise ValueError(f"Invalid role: {role}. Must be one of {VALID_ROLES}")

        data = self._load_data()
        agents = data.get("agents", {})
        if agent_id not in agents:
            raise ValueError(f"Agent '{agent_id}' not found in registry")

        agent = agents[agent_id]
        roles = agent.get("roles", [])
        if enabled:
            if role not in roles:
                roles.append(role)
        else:
            if role in roles:
                roles.remove(role)
        agent["roles"] = roles
        agents[agent_id] = agent
        data["agents"] = agents
        self._save_data(data)
        return agent

    def add_custom_agent(
        self,
        name: str,
        command: str,
        custom_path: Optional[str] = None,
        version_args: Optional[List[str]] = None,
        test_args: Optional[List[str]] = None,
        prompt_mode: str = "argument",
        timeout: int = 120,
        roles: Optional[List[str]] = None,
        declared_capabilities: Optional[Dict[str, bool]] = None
    ) -> Dict[str, Any]:
        agent_id = f"custom_{command.lower().replace('.', '_').replace(' ', '_').replace('-', '_')}"
        adapter = CustomAdapter(
            agent_id=agent_id,
            name=name,
            command=command,
            custom_path=custom_path,
            version_args=version_args,
            test_args=test_args,
            prompt_mode=prompt_mode,
            timeout=timeout,
            roles=roles,
            declared_capabilities=declared_capabilities
        )
        self._custom_adapters[agent_id] = adapter
        model = adapter.to_model(probe_ttl_seconds=self.probe_ttl_seconds)
        model.is_custom = True

        data = self._load_data()
        data.setdefault("agents", {})[agent_id] = model.model_dump(mode="json")
        self._save_data(data)
        return model.model_dump(mode="json")

    def delete_custom_agent(self, agent_id: str) -> bool:
        if agent_id in self._custom_adapters:
            del self._custom_adapters[agent_id]
        data = self._load_data()
        agents = data.get("agents", {})
        if agent_id in agents:
            del agents[agent_id]
            data["agents"] = agents
            self._save_data(data)
            return True
        return False
